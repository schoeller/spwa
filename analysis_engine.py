"""
Backend analysis engine for the Sheet Pile Wall Analysis Tool.

Contains the core classes and functions for performing geotechnical
calculations based on the free-earth support method.
"""

import copy
import numpy as np
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from scipy.integrate import cumulative_trapezoid, quad
from scipy.optimize import fsolve

from config import DEFAULT_CONFIG, NUM_PLOT_POINTS, MM_PER_M


@dataclass
class SoilLayer:
    """Represents a single soil layer with its geotechnical properties."""
    name: str
    thickness: float
    gamma: float
    gamma_sat: float
    phi: float
    cohesion: float

    def get_design_properties(self, fs_phi: float, fs_c: float) -> 'SoilLayer':
        """
        Applies factors of safety to friction angle and cohesion to get
        design properties.
        """
        phi_rad = np.radians(self.phi)
        if self.phi > 0 and fs_phi > 0:
            phi_d_rad = np.arctan(np.tan(phi_rad) / fs_phi)
        else:
            phi_d_rad = phi_rad
        c_d = self.cohesion / fs_c if fs_c > 0 else self.cohesion
        return SoilLayer(self.name, self.thickness, self.gamma, self.gamma_sat,
                         np.degrees(phi_d_rad), c_d)


class SoilProfile:
    """Manages the collection of soil layers and related calculations."""

    def __init__(self, layers_data: List[Dict[str, Any]], gamma_water: float):
        if not layers_data:
            raise ValueError("At least one soil layer is required.")
        self.layers = [SoilLayer(**data) for data in layers_data]
        self.gamma_water = gamma_water

    def get_properties_at_depth(
            self, z: float, design: bool = False,
            factors: Optional[Tuple[float, float]] = None) -> SoilLayer:
        """
        Retrieves the soil properties for a specific depth z.

        :param z: Depth below ground surface.
        :param design: If True, returns properties with safety factors applied.
        :param factors: Tuple of (fs_phi, fs_c).
        :return: A SoilLayer object for the specified depth.
        """
        current_depth = 0
        for layer in self.layers:
            if current_depth + layer.thickness > z:
                return layer.get_design_properties(*factors) \
                    if design and factors else layer
            current_depth += layer.thickness
        
        last_layer = self.layers[-1]
        return last_layer.get_design_properties(*factors) \
            if design and factors else last_layer

    def calculate_effective_stress(
            self, z: float, water_level: float) -> Tuple[float, float]:
        """
        Calculates the effective vertical stress and pore water pressure at depth z.

        :param z: Depth below ground surface.
        :param water_level: Depth of the water table.
        :return: A tuple of (effective_stress, pore_pressure).
        """
        sigma_v, current_depth = 0.0, 0.0
        if z < 0:
            return 0.0, 0.0

        for soil in self.layers:
            if z <= current_depth:
                break
            layer_top = current_depth
            layer_bottom = current_depth + soil.thickness
            calc_h = min(z, layer_bottom) - layer_top
            dry_h = max(0, min(calc_h, water_level - layer_top))
            wet_h = max(0, calc_h - dry_h)
            sigma_v += soil.gamma * dry_h + soil.gamma_sat * wet_h
            current_depth += soil.thickness

        pore_pressure = max(0, z - water_level) * self.gamma_water
        return sigma_v - pore_pressure, pore_pressure


class RetainingWall:
    """
    Represents the retaining wall, holding all structural, geometric,
    and load parameters.
    """

    def __init__(self, config: Dict[str, Any]):
        self._validate_inputs(config)
        self.config = config
        geo = config['geometry']
        loads = config['loads']
        opts = config['analysis_options']
        factors = config['factors']
        struct = config['structural_properties']

        # Geometric properties
        self.h = geo['excavation_depth_H']
        self.beta = np.radians(geo['backfill_slope_beta'])
        self.alpha = np.radians(geo['dredge_line_slope_alpha'])
        self.delta = np.radians(geo['wall_friction_delta'])

        # Load properties
        self.surcharge = loads['surcharge_load']
        self.hw_active = loads['water_level_active']
        self.hw_passive = loads['water_level_passive']

        # Analysis options
        self.anchor_depths = sorted(opts.get('anchor_depths', []))
        self.is_seismic = opts['is_seismic']
        self.kh = opts.get('kh', 0.0) if self.is_seismic else 0.0
        self.kv = opts.get('kv', 0.0) if self.is_seismic else 0.0

        # Structural properties
        self.e_modulus = struct['youngs_modulus_E']
        self._load_section_properties(config)
        self._calculate_allowable_stress(config)
        self.ei = self.e_modulus * self.i_moment

        # Factors of safety and other factors
        self.fs_phi = factors['FS_friction_angle']
        self.fs_c = factors['FS_cohesion']
        self.fs_bending = factors['FS_bending']
        self.embedment_factor = factors['embedment_increase_factor']
        self.rounding_increment = factors.get('rounding_increment', 0.1)

        # Soil profile
        self.soil_profile = SoilProfile(
            config['soil_profile'], config['constants']['gamma_water'])

    def _load_section_properties(self, config: Dict[str, Any]):
        """Loads I and W for the selected sheet pile section from the database."""
        struct_props = config['structural_properties']
        manufacturer = struct_props['selected_manufacturer']
        selected_model = struct_props['selected_section_model']
        db = config.get('section_database', {})

        if manufacturer not in db:
            raise ValueError(f"Manufacturer '{manufacturer}' not in database.")

        section_data = next(
            (s for s in db[manufacturer] if s["model"] == selected_model), None)

        if section_data is None:
            raise ValueError(
                f"Section '{selected_model}' from '{manufacturer}' not in database.")

        self.i_moment = section_data['moment_of_inertia_I']
        self.w_modulus = section_data['section_modulus_W']
        self.selected_section_model = selected_model

    def _calculate_allowable_stress(self, config: Dict[str, Any]):
        """Calculates allowable bending stress based on steel grade and FS."""
        struct_props = config['structural_properties']
        factors = config['factors']
        steel_grade = struct_props['selected_steel_grade']
        steel_db = struct_props.get('steel_grades', {})
        fy_yield = steel_db.get(steel_grade)
        fs = factors.get('FS_bending')

        if fy_yield is None:
            raise ValueError(f"Steel grade '{steel_grade}' not in database.")
        if fs is None or fs <= 1.0:
            raise ValueError("'FS_bending' must be > 1.0.")

        self.f_allowable = fy_yield / fs
        self.selected_steel_grade = steel_grade
        self.fy_yield = fy_yield

    def _validate_inputs(self, config: Dict[str, Any]):
        """Basic validation for critical input parameters."""
        if config['geometry']['excavation_depth_H'] <= 0:
            raise ValueError("Excavation depth H must be positive.")
        for depth in config['analysis_options'].get('anchor_depths', []):
            if depth >= config['geometry']['excavation_depth_H']:
                raise ValueError(
                    f"Anchor depth {depth}m must be less than H.")


class AnalysisEngine:
    """
    Performs the main sheet pile analysis, including calculating pressures,
    embedment depth, anchor forces, and internal forces/displacements.
    """

    def __init__(self, wall: RetainingWall):
        self.wall = wall
        self.d_required: Optional[float] = None
        self.d_design: Optional[float] = None
        self.t_anchors: Dict[float, float] = {}
        self.results: Dict[str, Any] = {}
        self.is_cantilever = not bool(wall.anchor_depths)

    def _robust_quad(self, func, a, b):
        """
        A more robust numerical integration that splits the integration
        domain at known discontinuities (soil layer boundaries, water levels).
        """
        w = self.wall
        points = {a, b}
        
        for p in [w.h, w.hw_active, w.hw_passive]:
            if a < p < b:
                points.add(p)

        current_depth = 0
        for layer in w.soil_profile.layers:
            current_depth += layer.thickness
            if a < current_depth < b:
                points.add(current_depth)

        integration_points = sorted(list(points))
        total_integral = 0
        for i in range(len(integration_points) - 1):
            start, end = integration_points[i], integration_points[i + 1]
            if start < end:
                integral, _ = quad(func, start, end, limit=100)
                total_integral += integral
        return total_integral, 0.0  

    def _get_pressure_coeffs(self, phi_deg: float) -> Tuple[float, float]:
        """
        Calculates active (Ka) and passive (Kp) earth pressure coefficients.
        Includes Mononobe-Okabe formulation for seismic conditions.
        """
        phi, w = np.radians(phi_deg), self.wall

        # Mononobe-Okabe for seismic conditions
        if w.is_seismic and w.kh > 0:
            theta = np.arctan(w.kh / (1 - w.kv)) if (1 - w.kv) != 0 else np.pi/2
            
            # K_AE (Active Seismic)
            kae_num_term = np.sin(phi + w.delta) * np.sin(phi - w.beta - theta)
            kae_den_term = np.cos(w.delta) * np.cos(w.beta)
            if kae_num_term < 0 or kae_den_term <= 0:
                kae_num_term = 0  # Avoid math domain error
            
            kae_sqrt_term = np.sqrt(kae_num_term / kae_den_term)
            kae_denominator = np.cos(theta) * (1 + kae_sqrt_term)**2
            kae = (np.cos(phi - theta)**2) / kae_denominator
            
            # K_PE (Passive Seismic)
            kpe_num_term = np.sin(phi + w.delta) * np.sin(phi + w.alpha - theta)
            kpe_den_term = np.cos(w.delta) * np.cos(w.alpha)
            if kpe_num_term < 0 or kpe_den_term <= 0:
                kpe_num_term = 0
            
            kpe_sqrt_term = np.sqrt(kpe_num_term / kpe_den_term)
            kpe_denominator = np.cos(theta) * (1 - kpe_sqrt_term)**2
            kpe = (np.cos(phi - theta)**2) / kpe_denominator
            
            return kae, kpe
            
        # Coulomb's theory for static conditions
        ka_den = np.sin(np.pi / 2 - w.delta) * (
            1 + np.sqrt(
                np.sin(phi + w.delta) * np.sin(phi - w.beta) /
                (np.sin(np.pi / 2 - w.delta) * np.sin(np.pi / 2 + w.beta))
            )
        )**2
        ka = (np.sin(np.pi / 2 + phi)**2) / (np.sin(np.pi / 2)**2 * ka_den)
        
        kp_den = np.sin(np.pi / 2 + w.delta) * (
            1 - np.sqrt(
                np.sin(phi + w.delta) * np.sin(phi + w.alpha) /
                (np.sin(np.pi / 2 + w.delta) * np.sin(np.pi / 2 + w.alpha))
            )
        )**2
        kp = (np.sin(np.pi / 2 - phi)**2) / (np.sin(np.pi / 2)**2 * kp_den)
        
        return ka, kp

    def _calculate_pressure_at_depth(self, z: float) -> Dict[str, float]:
        """Calculates active and passive pressures at a specific depth z."""
        factors = (self.wall.fs_phi, self.wall.fs_c)
        soil_d_act = self.wall.soil_profile.get_properties_at_depth(
            z, True, factors)
        sig_v_eff, u_act = self.wall.soil_profile.calculate_effective_stress(
            z, self.wall.hw_active)
        ka, _ = self._get_pressure_coeffs(soil_d_act.phi)
        p_earth_act = max(
            0, ka * (sig_v_eff + self.wall.surcharge) -
            2 * soil_d_act.cohesion * np.sqrt(ka)
        )
        p_total_act = p_earth_act + u_act

        p_earth_pass, p_total_pass, u_pass = 0.0, 0.0, 0.0
        if z > self.wall.h:
            soil_d_pass = self.wall.soil_profile.get_properties_at_depth(
                z, True, factors)
            # Effective stress for passive side is calculated from dredge line
            sig_v_eff_pass, u_pass = \
                self.wall.soil_profile.calculate_effective_stress(
                    z - self.wall.h, self.wall.hw_passive - self.wall.h)
            _, kp = self._get_pressure_coeffs(soil_d_pass.phi)
            p_earth_pass = max(
                0, kp * sig_v_eff_pass +
                2 * soil_d_pass.cohesion * np.sqrt(kp)
            )
            p_total_pass = p_earth_pass + u_pass

        return {
            'active': p_total_act, 'passive': p_total_pass,
            'earth_active': p_earth_act, 'earth_passive': p_earth_pass,
            'water_active': u_act, 'water_passive': u_pass
        }

    def _moment_balance_equation(self, depth: float) -> float:
        """
        The core equation for the free-earth support method. The solver finds
        the depth `d` where the net moment is zero.
        """
        if depth <= 0:
            return 1e6  # Return a large number for invalid depths

        # Reference point for moment calculation
        if self.is_cantilever:
            # For cantilever walls, moment is taken about the toe
            moment_ref_z = self.wall.h + depth
        else:
            # For anchored walls, moment is taken about the lowest anchor
            moment_ref_z = self.wall.anchor_depths[-1]

        moment_arm = lambda z: (z - moment_ref_z)

        m_act, _ = self._robust_quad(
            lambda z: self._calculate_pressure_at_depth(z)['active'] * moment_arm(z),
            0, self.wall.h + depth
        )
        m_pass, _ = self._robust_quad(
            lambda z: self._calculate_pressure_at_depth(z)['passive'] * moment_arm(z),
            self.wall.h, self.wall.h + depth
        )

        return m_act - m_pass

    def run(self):
        """Main execution function to run the complete analysis."""
        solution, _, ier, _ = fsolve(
            lambda d: self._moment_balance_equation(d[0]),
            [self.wall.h * 0.8],  # Initial guess
            full_output=True
        )
        if ier != 1:
            raise RuntimeError("Solver for embedment depth failed to converge!")

        self.d_required = solution[0]
        self.d_design = np.ceil(
            self.d_required * self.wall.embedment_factor /
            self.wall.rounding_increment
        ) * self.wall.rounding_increment

        if not self.is_cantilever:
            self._calculate_anchor_forces()

        self._calculate_diagrams()
        self._perform_stress_check()
        self._perform_deflection_check()

    def _calculate_anchor_forces(self):
        """Calculates anchor forces based on horizontal force equilibrium."""
        total_length = self.wall.h + self.d_design
        f_active, _ = self._robust_quad(
            lambda z: self._calculate_pressure_at_depth(z)['active'],
            0, total_length
        )
        f_passive, _ = self._robust_quad(
            lambda z: self._calculate_pressure_at_depth(z)['passive'],
            self.wall.h, total_length
        )
        t_total = max(0, f_active - f_passive)
        n = len(self.wall.anchor_depths)

        if n == 1:
            self.t_anchors[self.wall.anchor_depths[0]] = t_total
            return

        # Distribute total force for multi-anchor systems (simplified approach)
        midpoints = [(self.wall.anchor_depths[i] + self.wall.anchor_depths[i + 1]) / 2
                     for i in range(n - 1)]
        boundaries = [0] + midpoints + [total_length]

        area_forces = [
            self._robust_quad(
                lambda z: self._calculate_pressure_at_depth(z)['active'] -
                self._calculate_pressure_at_depth(z)['passive'],
                boundaries[i], boundaries[i + 1]
            )[0] for i in range(n)
        ]

        total_area_force = sum(f for f in area_forces if f > 0)
        if total_area_force > 0:
            for i, depth in enumerate(self.wall.anchor_depths):
                self.t_anchors[depth] = (max(0, area_forces[i]) /
                                         total_area_force) * t_total
        else:
            # If no positive net force, distribute equally
            for depth in self.wall.anchor_depths:
                self.t_anchors[depth] = t_total / n

    def _calculate_diagrams(self):
        """
        Calculates shear, moment, rotation, and deflection diagrams by
        integrating the net pressure diagram.
        """
        z = np.linspace(0, self.wall.h + self.d_design, NUM_PLOT_POINTS)
        p_data = np.array([self._calculate_pressure_at_depth(zi) for zi in z])
        net_p = np.array([pi['active'] - pi['passive'] for pi in p_data])

        # Integrate for Shear
        v = cumulative_trapezoid(net_p, x=z, initial=0)
        if not self.is_cantilever:
            for depth, force in sorted(self.t_anchors.items()):
                if force > 0:
                    v[z >= depth] -= force

        # Integrate for Moment
        m = cumulative_trapezoid(v, x=z, initial=0)
        # Integrate for Curvature, Rotation, and Deflection
        c = m / self.wall.ei if self.wall.ei > 0 else np.zeros_like(m)
        r = cumulative_trapezoid(c, x=z, initial=0)
        d = cumulative_trapezoid(r, x=z, initial=0)
        d -= d[-1]  
        imax = np.argmax(np.abs(d))

        self.results = {
            'z_vals': z, 'net_pressure': net_p, 'shear': v, 'moment': m,
            'rotation': r, 'deflection': d, 'p_max': np.max(net_p),
            'p_min': np.min(net_p), 'm_max': np.max(m), 'm_min': np.min(m),
            'v_max': np.max(v), 'v_min': np.min(v), 'rot_max': np.max(r),
            'rot_min': np.min(r), 'delta_max': d[imax],
            
            'earth_pressure_active': np.array([p['earth_active'] for p in p_data]),
            'earth_pressure_passive': np.array([p['earth_passive'] for p in p_data]),
            'water_pressure_active': np.array([p['water_active'] for p in p_data]),
            'water_pressure_passive': np.array([p['water_passive'] for p in p_data])
        }
        self.results['rot_max_abs'] = max(abs(self.results['rot_max']),
                                           abs(self.results['rot_min']))

    def _perform_stress_check(self):
        """Checks if the maximum bending stress exceeds the allowable stress."""
        m_max_abs = max(abs(self.results['m_max']), abs(self.results['m_min']))
        actual_stress = m_max_abs / self.wall.w_modulus \
            if self.wall.w_modulus > 1e-9 else float('inf')

        if actual_stress <= self.wall.f_allowable:
            status = "OK"
        else:
            status = "NOT OK - STRESS EXCEEDED!"

        self.results.update({
            'm_max_abs': m_max_abs,
            'actual_stress': actual_stress,
            'stress_check_status': status
        })

    def _perform_deflection_check(self):
        """Checks if the maximum deflection exceeds the code-based limit."""
        delta_max_abs_mm = abs(self.results['delta_max'] * MM_PER_M)
        selected_code = self.wall.config['analysis_options']['deflection_check_code']
        code_db = self.wall.config['deflection_codes']
        divisor = code_db.get(selected_code)

        if divisor is None:
            status = "N/A"
            allowable_deflection_mm = float('inf')
        else:
            allowable_deflection_mm = (self.wall.h / divisor) * MM_PER_M
            status = "OK" if delta_max_abs_mm <= allowable_deflection_mm \
                else "NOT OK - DEFLECTION EXCEEDED!"

        self.results.update({
            'deflection_check_status': status,
            'allowable_deflection': allowable_deflection_mm,
            'actual_max_deflection': delta_max_abs_mm
        })

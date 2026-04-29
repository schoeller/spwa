import unittest
import numpy as np
import sys
import os

# Add the parent directory to the Python path to import the main modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analysis_engine import SoilLayer, SoilProfile, RetainingWall, AnalysisEngine
from config import DEFAULT_CONFIG

class TestSoilClasses(unittest.TestCase):

    def setUp(self):
        """Set up common resources for tests."""
        self.layer_data1 = {"name": "Sand", "thickness": 10.0, "gamma": 18.0,
                              "gamma_sat": 20.0, "phi": 30.0, "cohesion": 0}
        self.layer_data2 = {"name": "Clay", "thickness": 5.0, "gamma": 17.0,
                              "gamma_sat": 19.0, "phi": 20.0, "cohesion": 15}
        self.soil_layer1 = SoilLayer(**self.layer_data1)
        self.soil_profile = SoilProfile([self.layer_data1, self.layer_data2], gamma_water=9.81)

    def test_soil_layer_creation(self):
        """Test the initialization of a SoilLayer object."""
        self.assertEqual(self.soil_layer1.name, "Sand")
        self.assertEqual(self.soil_layer1.phi, 30.0)

    def test_get_design_properties(self):
        """Test the application of safety factors to soil properties."""
        fs_phi, fs_c = 1.25, 1.5
        design_layer = self.soil_layer1.get_design_properties(fs_phi, fs_c)

        # Check if phi is correctly reduced
        expected_phi_d = np.degrees(np.arctan(np.tan(np.radians(30)) / fs_phi))
        self.assertAlmostEqual(design_layer.phi, expected_phi_d)

        # Check that cohesion remains 0
        self.assertEqual(design_layer.cohesion, 0)

        # Check with non-zero cohesion
        clay_layer = SoilLayer(**self.layer_data2)
        design_clay = clay_layer.get_design_properties(fs_phi, fs_c)
        self.assertAlmostEqual(design_clay.cohesion, 15.0 / fs_c)

    def test_get_properties_at_depth(self):
        """Test retrieving soil properties at a specific depth."""
        # Test within the first layer
        props_at_5m = self.soil_profile.get_properties_at_depth(5)
        self.assertEqual(props_at_5m.name, "Sand")

        # Test at the boundary
        props_at_10m = self.soil_profile.get_properties_at_depth(10)
        self.assertEqual(props_at_10m.name, "Clay")

        # Test within the second layer
        props_at_12m = self.soil_profile.get_properties_at_depth(12)
        self.assertEqual(props_at_12m.name, "Clay")

        # Test beyond the profile depth
        props_at_20m = self.soil_profile.get_properties_at_depth(20)
        self.assertEqual(props_at_20m.name, "Clay") # Should return the last layer

    def test_calculate_effective_stress(self):
        """Test the calculation of effective vertical stress and pore pressure."""
        # Case 1: Depth within the first layer, above water table
        stress, pressure = self.soil_profile.calculate_effective_stress(z=4, water_level=12)
        self.assertAlmostEqual(stress, 4 * 18.0)
        self.assertEqual(pressure, 0)

        # Case 2: Depth within the first layer, below water table
        stress, pressure = self.soil_profile.calculate_effective_stress(z=8, water_level=5)
        expected_stress = (5 * 18.0) + (3 * 20.0) - (3 * 9.81)
        self.assertAlmostEqual(stress, expected_stress)
        self.assertAlmostEqual(pressure, 3 * 9.81)

        # Case 3: Depth within the second layer, below water table
        stress, pressure = self.soil_profile.calculate_effective_stress(z=12, water_level=5)
        sigma_v = (5 * 18.0) + (5 * 20.0) + (2 * 19.0)
        u = (12 - 5) * 9.81
        self.assertAlmostEqual(stress, sigma_v - u)
        self.assertAlmostEqual(pressure, u)

class TestAnalysisEngine(unittest.TestCase):

    def setUp(self):
        """Set up a default configuration for the analysis engine tests."""
        self.config = DEFAULT_CONFIG.copy()
        # Use a simple, predictable soil profile for most tests
        self.config['soil_profile'] = [
            {"name": "Uniform Sand", "thickness": 50.0, "gamma": 18.0,
             "gamma_sat": 20.0, "phi": 35.0, "cohesion": 0}
        ]
        self.config['geometry']['excavation_depth_H'] = 6.0
        self.config['loads']['surcharge_load'] = 10.0
        self.config['loads']['water_level_active'] = 100.0 # Dry
        self.config['loads']['water_level_passive'] = 100.0 # Dry
        self.config['analysis_options']['anchor_depths'] = [] # Cantilever
        self.config['analysis_options']['is_seismic'] = False


    def test_retaining_wall_initialization(self):
        """Test the initialization of the RetainingWall object."""
        wall = RetainingWall(self.config)
        self.assertEqual(wall.h, 6.0)
        self.assertEqual(wall.surcharge, 10.0)
        self.assertFalse(wall.is_seismic)
        self.assertAlmostEqual(wall.f_allowable, 355000 / 1.5)

    def test_pressure_coeffs_static(self):
        """Test Coulomb's pressure coefficients for static conditions."""
        wall = RetainingWall(self.config)
        # Using common values for delta and beta for validation
        wall.delta = np.radians(2/3 * 35) # delta = 2/3 * phi
        wall.beta = np.radians(0) # horizontal backfill
        wall.alpha = np.radians(0) # horizontal dredge line

        engine = AnalysisEngine(wall)
        ka, kp = engine._get_pressure_coeffs(phi_deg=35)

        # Values calculated from the implemented Coulomb formulas
        self.assertAlmostEqual(ka, 0.244, places=3)
        self.assertAlmostEqual(kp, 9.962, places=3)

    def test_pressure_coeffs_seismic(self):
        """Test Mononobe-Okabe pressure coefficients for seismic conditions."""
        self.config['analysis_options']['is_seismic'] = True
        self.config['analysis_options']['kh'] = 0.2
        wall = RetainingWall(self.config)
        wall.delta = np.radians(0) # Simplified for M-O comparison
        wall.beta = np.radians(0)
        wall.alpha = np.radians(0)

        engine = AnalysisEngine(wall)
        kae, kpe = engine._get_pressure_coeffs(phi_deg=35)

        # Values calculated from the implemented Mononobe-Okabe formulas
        self.assertAlmostEqual(kae, 0.390, places=3)
        self.assertAlmostEqual(kpe, 3.163, places=3)


if __name__ == '__main__':
    unittest.main()
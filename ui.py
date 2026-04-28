"""
Modern UI components for the Sheet Pile Wall Analysis Tool.

This file contains the redesigned main window, sidebar, collapsible groups,
and plot displays, now with integrated SVG icons.
"""

import sys
import copy
import json
from pathlib import Path  

import matplotlib
matplotlib.use('QtAgg')

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_qtagg import (FigureCanvasQTAgg as
                                               FigureCanvas)
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QFont, QIcon  
from PyQt6.QtWidgets import (QApplication, QCheckBox, QComboBox,
                             QDoubleSpinBox, QFileDialog, QFormLayout,
                             QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                             QMainWindow, QMessageBox, QPlainTextEdit,
                             QPushButton, QScrollArea, QTabWidget,
                             QVBoxLayout, QWidget, QToolButton,
                             QAbstractSpinBox)

from config import DEFAULT_CONFIG, TRANSLATIONS
from analysis_engine import RetainingWall, AnalysisEngine


ICON_ROOT = Path(__file__).parent / "icons"


class MplCanvas(FigureCanvas):
    """A custom Matplotlib canvas widget for PyQt6 integration."""
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(10, 8), dpi=100)
        super().__init__(self.fig)


class AnchorInputWidget(QWidget):
    """A widget for inputting a single anchor depth."""
    removed = pyqtSignal(object)

    def __init__(self, depth: float, lang_dict: dict):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)

        self.depth_label = QLabel()
        self.depth_input = QDoubleSpinBox(
            decimals=2, maximum=100.0, value=depth)
        self.depth_input.setButtonSymbols(
            QAbstractSpinBox.ButtonSymbols.NoButtons)

        self.remove_button = QPushButton()
        self.remove_button.setIcon(QIcon(str(ICON_ROOT / "x-circle.svg"))) 
        self.remove_button.clicked.connect(lambda: self.removed.emit(self))

        layout.addWidget(self.depth_label)
        layout.addWidget(self.depth_input, 1)
        layout.addWidget(self.remove_button)
        self.setLayout(layout)
        self.update_language(lang_dict)

    def get_depth(self) -> float:
        return self.depth_input.value()

    def update_language(self, lang_dict: dict):
        self.depth_label.setText(lang_dict["depth"])
        self.remove_button.setText("")
        self.remove_button.setToolTip(lang_dict["remove"]) 


class SoilLayerWidget(QWidget):
    """A widget for inputting the properties of a single soil layer."""
    removed = pyqtSignal(object)

    def __init__(self, layer_data: dict, lang_dict: dict,
                 is_first_layer: bool = False):
        super().__init__()
        self.labels, self.inputs = {}, {}
        main_layout = QVBoxLayout()
        self.group = QGroupBox()
        main_layout.setContentsMargins(0, 5, 0, 5)
        main_layout.addWidget(self.group)
        layout = QFormLayout(self.group)

        self.inputs['name'] = QLineEdit(layer_data.get("name", "Soil Layer"))
        self.inputs['thickness'] = QDoubleSpinBox(
            decimals=2, maximum=500.0, value=layer_data.get("thickness", 10.0))
        self.inputs['gamma'] = QDoubleSpinBox(
            decimals=2, maximum=30.0, value=layer_data.get("gamma", 18.0))
        self.inputs['gamma_sat'] = QDoubleSpinBox(
            decimals=2, maximum=30.0, value=layer_data.get("gamma_sat", 20.0))
        self.inputs['phi'] = QDoubleSpinBox(
            decimals=2, maximum=90.0, value=layer_data.get("phi", 30.0))
        self.inputs['cohesion'] = QDoubleSpinBox(
            decimals=2, maximum=500.0, value=layer_data.get("cohesion", 0.0))

        for w in self.inputs.values():
            if isinstance(w, QDoubleSpinBox):
                w.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        self.remove_button = QPushButton()
        self.remove_button.setIcon(QIcon(str(ICON_ROOT / "x-circle.svg"))) 
        self.remove_button.clicked.connect(lambda: self.removed.emit(self))
        self.remove_button.setEnabled(not is_first_layer)

        for key, text_key in [('name', 'layer_name'), ('thickness', 'thickness'),
                              ('gamma', 'unit_weight'),
                              ('gamma_sat', 'sat_unit_weight'),
                              ('phi', 'friction_angle'),
                              ('cohesion', 'cohesion')]:
            self.labels[key] = QLabel()
            layout.addRow(self.labels[key], self.inputs[key])
        layout.addRow(self.remove_button)
        self.setLayout(main_layout)
        self.update_language(lang_dict)

    def get_data(self) -> dict:
        return {k: w.value() if isinstance(w, QDoubleSpinBox) else w.text()
                for k, w in self.inputs.items()}

    def update_language(self, lang_dict: dict):
        for key, text_key in [('name', 'layer_name'), ('thickness', 'thickness'),
                              ('gamma', 'unit_weight'),
                              ('gamma_sat', 'sat_unit_weight'),
                              ('phi', 'friction_angle'),
                              ('cohesion', 'cohesion')]:
            self.labels[key].setText(lang_dict[text_key])
        self.remove_button.setText(lang_dict["remove_layer"])
        self.remove_button.setToolTip(lang_dict["remove_layer"]) 

class Plotter:
    def __init__(self, wall: RetainingWall, analysis: AnalysisEngine,
                 lang_dict: dict):
        self.wall = wall
        self.analysis = analysis
        self.results = analysis.results
        self.lang_dict = lang_dict
        self.l_total = wall.h + analysis.d_design

    def _create_base_figure_and_axes(self, fig: Figure, title: str):
        """Creates axes on the provided figure object."""
        
        axes = fig.subplots(
            1, 2,
            gridspec_kw={'width_ratios': [1, 1]}
        )
        self._format_figure(fig, axes, title)
        return axes

    def _format_figure(self, fig: plt.Figure, axes: list[plt.Axes], title: str):
        title_info = self.wall.config['project_info']
        analysis_type = self.lang_dict["anchored_wall"] if \
            not self.analysis.is_cantilever else self.lang_dict["cantilever_wall"]
        seismic = (f"({self.lang_dict['seismic']}, kh={self.wall.kh})"
                   if self.wall.is_seismic else f"({self.lang_dict['static']})")
        # main_title = f"{title_info.get('title')}\n{analysis_type} {seismic}"
        main_title = f"{self.lang_dict.get('project_title_prefix', '')}{title_info.get('title', '')}\n{analysis_type} {seismic}"
        fig.suptitle(main_title, fontsize=14, y=0.99)

        axes[1].set_title(
            f"{title}\n{self.lang_dict['section']}: "
            f"{self.wall.selected_section_model} ({self.wall.selected_steel_grade})",
            fontsize=11)

        bottom_lim = self.l_total * 1.05
        top_lim = -self.l_total * 0.05
        for ax in axes:
            ax.set_ylim(bottom_lim, top_lim)

        axes[0].tick_params(axis='y', labelleft=True)
        axes[1].tick_params(axis='y', labelleft=False)
        fig.tight_layout(rect=[0.03, 0.03, 0.97, 0.90])

    def setup_plot(self, plot_key: str, figure: Figure):
        """Configures and draws a specific plot onto the provided figure."""
        plot_configs = {
            'net_pressure': {'title_key': 'tab_net_pressure', 'data_key': 'net_pressure',
                             'xlabel': 'kPa', 'color': 'b', 'annotations': [('p_max', 'max'), ('p_min', 'min')]},
            'earth_pressure': {'title_key': 'tab_earth_pressure', 'xlabel': 'kPa'},
            'water_pressure': {'title_key': 'tab_water_pressure', 'xlabel': 'kPa'},
            'shear': {'title_key': 'tab_shear', 'data_key': 'shear',
                      'xlabel': 'kN/m', 'color': 'g', 'annotations': [('v_max', 'max'), ('v_min', 'min')]},
            'moment': {'title_key': 'tab_moment', 'data_key': 'moment',
                       'xlabel': 'kNm/m', 'color': 'm', 'annotations': [('m_max', 'max'), ('m_min', 'min')]},
            'rotation': {'title_key': 'tab_rotation', 'data_key': 'rotation',
                         'xlabel': 'rad', 'color': 'c', 'annotations': [('rot_max_abs', 'max_abs', 1, "max_abs_rotation")]},
            'deflection': {'title_key': 'tab_deflection', 'data_key': 'deflection',
                           'xlabel': 'mm', 'color': 'orange', 'annotations': [('delta_max', 'max_abs', 1000, "max_deflection")]}
        }
        config = plot_configs[plot_key]
        
        axes = self._create_base_figure_and_axes(
            figure, self.lang_dict[config['title_key']])
        self._plot_schematic(axes[0])

        if plot_key == 'earth_pressure':
            self._plot_dual_diagram(
                axes[1], self.results['earth_pressure_active'],
                self.results['earth_pressure_passive'], config['xlabel'],
                self.lang_dict['earth_active'], self.lang_dict['earth_passive'],
                'r', 'g'
            )
        elif plot_key == 'water_pressure':
            self._plot_dual_diagram(
                axes[1], self.results['water_pressure_active'],
                self.results['water_pressure_passive'], config['xlabel'],
                self.lang_dict['water_active'],
                self.lang_dict['water_passive'], 'b', 'cyan'
            )
        else:
            multiplier = 1000 if plot_key == 'deflection' else 1
            data_to_plot = self.results[config['data_key']] * multiplier
            self._plot_diagram(
                axes[1], data_to_plot,
                config['xlabel'], config['color']
            )
            for ann_config in config['annotations']:
                res_key, pos, *rest = ann_config
               
                value_for_label = self.results[res_key]
                label_key = rest[1] if len(rest) > 1 else res_key
                label_text = f"{self.lang_dict.get(label_key, label_key)} = {value_for_label:.2f}"
                if "rotation" in label_key:
                    label_text = f"{self.lang_dict.get(label_key, label_key)} = {value_for_label:.4f}"
                elif "deflection" in label_key:
                     label_text = f"{self.lang_dict.get(label_key, label_key)} = {value_for_label*1000:.2f} mm"

                self._annotate_diagram(
                    axes[1], data_to_plot, label_text, pos)
        

    def _annotate_diagram(self, ax, data, label, position):
        if abs(np.max(np.abs(data))) < 1e-6:
            return

        if position == 'max_abs':
            idx = np.argmax(np.abs(data))
        elif position == 'max':
            idx = np.argmax(data)
        else:
            idx = np.argmin(data)

        annot_val, annot_y = data[idx], self.results['z_vals'][idx]
        
        xlims = ax.get_xlim()
        x_range = xlims[1] - xlims[0]
        if abs(x_range) < 1e-9: x_range = 1 
        x_pos_ratio = (annot_val - xlims[0]) / x_range
        
        if x_pos_ratio > 0.8:
            ha, x_offset = 'right', -25
        elif x_pos_ratio < 0.2:
            ha, x_offset = 'left', 25
        else:
            ha = 'left' if annot_val >= 0 else 'right'
            x_offset = 25 if annot_val >= 0 else -25

        va = 'bottom' if position != 'min' else 'top'
        y_offset = 25 if position != 'min' else -25

        ax.annotate(
            label, xy=(annot_val, annot_y), xytext=(x_offset, y_offset),
            textcoords='offset points', ha=ha, va=va,
            bbox={'boxstyle': "round,pad=0.3", 'fc': "wheat", 'alpha': 0.85},
            arrowprops={'arrowstyle': "->", 'connectionstyle': "arc3,rad=0.2"},
            fontsize=8
        )
        
    def _plot_diagram(self, ax, data, xlabel, color):
        ax.set_xlabel(xlabel, fontsize=10)
        ax.plot(data, self.results['z_vals'], color=color)
        ax.axhline(self.wall.h, color='r', ls='--', lw=1)
        ax.axvline(0, color='k', ls='-', lw=0.8)
        ax.fill_betweenx(self.results['z_vals'], data, 0, color=color, alpha=0.2)
        ax.grid(True, linestyle=':', alpha=0.6)
        min_val, max_val = np.min(data), np.max(data)
        margin = max(abs(min_val), abs(max_val)) * 0.3
        if margin < 1e-9: margin = 0.1 
        ax.set_xlim(min_val - margin, max_val + margin)

    def _plot_dual_diagram(self, ax, data1, data2, xlabel, label1, label2,
                           color1, color2):
        ax.set_xlabel(xlabel, fontsize=10)
        ax.plot(data1, self.results['z_vals'], color=color1, label=label1)
        ax.fill_betweenx(self.results['z_vals'], data1, 0, color=color1, alpha=0.2)
        ax.plot(-data2, self.results['z_vals'], color=color2, label=label2)
        ax.fill_betweenx(self.results['z_vals'], -data2, 0, color=color2, alpha=0.2)
        ax.axhline(self.wall.h, color='r', ls='--', lw=1)
        ax.axvline(0, color='k', ls='-', lw=0.8)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend(fontsize=8)
        min_val = -np.max(data2) if len(data2) > 0 else 0
        max_val = np.max(data1) if len(data1) > 0 else 0
        margin = max(abs(min_val), abs(max_val)) * 0.1
        if margin < 1e-9: margin = 0.1
        ax.set_xlim(min_val - margin, max_val + margin)

    def _plot_schematic(self, ax: plt.Axes):
        sw, wall_x, w = 1.3, -0.1, self.wall
        ax.set_title(self.lang_dict["schematic_title"], fontsize=12)
        ax.set_xlim(-sw, sw)
        ax.set_xticks([])
        ax.set_ylabel(self.lang_dict["depth_m"], fontsize=10)
        
        by = -np.tan(w.beta) * (sw + wall_x)
        active_poly = [(wall_x, 0), (-sw, by), (-sw, self.l_total), (wall_x, self.l_total)]
        ax.add_patch(patches.Polygon(active_poly, fc='sandybrown', alpha=0.6, hatch='..'))
        
        dy = w.h + np.tan(w.alpha) * (sw - (wall_x + 0.2))
        passive_poly = [(wall_x + 0.2, w.h), (sw, dy), (sw, self.l_total), (wall_x + 0.2, self.l_total)]
        ax.add_patch(patches.Polygon(passive_poly, fc='sandybrown', alpha=0.6, hatch='..'))
        
        ax.add_patch(patches.Rectangle((wall_x, 0), 0.2, self.l_total, fc='gray', ec='black', zorder=10))
        
        ax.axhline(w.hw_active, color='blue', ls='--', xmin=0.05, xmax=0.45, label=self.lang_dict["water_active"])
        ax.axhline(w.hw_passive, color='cyan', ls=':', xmin=0.55, xmax=0.95, label=self.lang_dict["water_passive"])
        ax.axhline(w.h, color='red', ls='-', lw=2, xmin=0.55, xmax=1.0, label=self.lang_dict["dredge_line"])
        
        if not self.analysis.is_cantilever:
            for depth, force in self.analysis.t_anchors.items():
                ax.plot([-0.5, wall_x], [depth, depth], 'k-', lw=2, zorder=11)
                ax.text(-0.5, depth, f" T={force:.1f}", ha='right', va='bottom', fontsize=8,
                        zorder=12, bbox={'fc': 'white', 'alpha': 0.7})
                        
        self._draw_dimension_line(ax, 0.9, 0, w.h, f"H = {w.h:.2f} m")
        self._draw_dimension_line(ax, 0.9, w.h, self.l_total, f"D = {self.analysis.d_design:.2f} m")
        
        ax.legend(loc='lower left', fontsize=8)
        ax.grid(False)

    def _draw_dimension_line(self, ax, x, y1, y2, label):
        ax.arrow(x, y1, 0, y2 - y1, head_width=0.04, head_length=0.2, fc='k', ec='k')
        ax.arrow(x, y2, 0, y1 - y2, head_width=0.04, head_length=0.2, fc='k', ec='k')
        ax.text(x + 0.05, (y1 + y2) / 2, f" {label} ", ha='left', va='center', rotation=90,
                bbox={'fc': 'white', 'ec': 'none', 'alpha': 0.8}, fontsize=8)


class MainWindow(QMainWindow):
    """The main application window, orchestrating the UI and analysis."""

    def __init__(self):
        super().__init__()
        self.current_lang = "en"
        self.current_wall = None
        self.current_analysis = None
        self.inputs, self.groups, self.labels, self.input_tabs = {}, {}, {}, {}
        self.plot_canvases, self.save_plot_actions = {}, {}
        
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout(self.main_widget)

        self._set_stylesheet()
        self._create_menu_bar()
        self._create_input_panel()
        self._create_output_panel()

        self.main_layout.addWidget(self.input_tabs_widget, 1)
        self.main_layout.addWidget(self.output_tabs, 2)

        self.update_ui_language()
        
        self.is_dark_theme = True 
        self.toggle_theme()

    def _set_stylesheet(self):
        self.setFont(QFont("Segoe UI", 9))
        self.dark_theme = """
            QMainWindow, QWidget { background-color: #2D2D2D; color: #DDD; }
            QGroupBox { border: 1px solid #555; border-radius: 4px; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; color: #BBB;}
            QLabel, QCheckBox { color: #DDD; background-color: transparent; }
            QLineEdit, QDoubleSpinBox, QComboBox { background-color: #3D3D3D; color: #EEE; border: 1px solid #666; border-radius: 3px; padding: 4px; }
            QPushButton, QToolButton { background-color: #555; color: #EEE; border: 1px solid #666; border-radius: 3px; padding: 5px 10px; }
            QPushButton:hover, QToolButton:hover { background-color: #666; }
            QPushButton:pressed, QToolButton:pressed { background-color: #4A4A4A; }
            QTabWidget::pane { border: 1px solid #555; }
            QTabBar::tab { background: #3D3D3D; color: #CCC; padding: 8px 20px; border: 1px solid #555; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px;}
            QTabBar::tab:selected { background: #4D4D4D; color: #FFF; }
            QScrollArea { border: none; background-color: transparent; }
            QPlainTextEdit { background-color: #222; color: #DDD; border: 1px solid #555; font-family: "Courier New"; }
        """
        self.light_theme = """
            QMainWindow, QWidget { background-color: #f0f0f0; color: #333; }
            QGroupBox { border: 1px solid #ccc; border-radius: 4px; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; color: #555;}
            QLabel, QCheckBox { color: #333; background-color: transparent; }
            QLineEdit, QDoubleSpinBox, QComboBox { background-color: #fff; color: #333; border: 1px solid #ccc; border-radius: 3px; padding: 4px; }
            QPushButton, QToolButton { background-color: #e0e0e0; color: #333; border: 1px solid #ccc; border-radius: 3px; padding: 5px 10px; }
            QPushButton:hover, QToolButton:hover { background-color: #d0d0d0; }
            QPushButton:pressed, QToolButton:pressed { background-color: #c0c0c0; }
            QTabWidget::pane { border: 1px solid #ccc; }
            QTabBar::tab { background: #e0e0e0; color: #555; padding: 8px 20px; border: 1px solid #ccc; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px;}
            QTabBar::tab:selected { background: #f0f0f0; color: #333; }
            QScrollArea { border: none; background-color: transparent; }
            QPlainTextEdit { background-color: #fff; color: #333; border: 1px solid #ccc; font-family: "Courier New"; }
        """

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        self.setStyleSheet(
            self.dark_theme if self.is_dark_theme else self.light_theme)
        self.theme_button.setText("☀️" if self.is_dark_theme else "🌙")

    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        self.file_menu = menu_bar.addMenu("")
        self.open_project_action = QAction(QIcon(str(ICON_ROOT / "folder.svg")), "", self)
        self.open_project_action.triggered.connect(self.open_project)
        self.file_menu.addAction(self.open_project_action)
        self.save_project_action = QAction(QIcon(str(ICON_ROOT / "save.svg")), "", self)
        self.save_project_action.triggered.connect(self.save_project)
        self.file_menu.addAction(self.save_project_action)
        self.file_menu.addSeparator()
        self.help_menu = menu_bar.addMenu("")
        self.about_action = QAction(QIcon(str(ICON_ROOT / "help-circle.svg")), "", self)
        self.about_action.triggered.connect(self._show_about_dialog)
        self.help_menu.addAction(self.about_action)
        self.exit_action = QAction(QIcon(str(ICON_ROOT / "log-out.svg")), "", self)
        self.exit_action.triggered.connect(self.close)

    def _show_about_dialog(self):
        lang = TRANSLATIONS[self.current_lang]
        QMessageBox.about(self, lang["about_title"], lang["about_text"])

    def _create_input_panel(self):
        self.input_tabs_widget = QTabWidget()
        self._create_project_analysis_tab()
        self._create_soil_tab()
        self._create_anchors_tab()
        self._create_structure_geometry_tab()
        self._create_loads_tab()

    def _create_tab(self, key):
        tab = QWidget()
        self.input_tabs[key] = tab
        self.input_tabs_widget.addTab(tab, "")
        layout = QVBoxLayout(tab)
        if key == "tab_project":
            header_layout = QHBoxLayout()
            self.labels['lang_label'] = QLabel()
            header_layout.addWidget(self.labels['lang_label'])
            self.lang_combo = QComboBox()
            self.lang_combo.addItems(["English", "Türkçe", "Deutsch"])
            self.lang_combo.currentIndexChanged.connect(self._language_changed)
            header_layout.addWidget(self.lang_combo)
            header_layout.addStretch(1)
            self.theme_button = QToolButton()
            self.theme_button.clicked.connect(self.toggle_theme)
            header_layout.addWidget(self.theme_button)
            layout.addLayout(header_layout)
        return layout

    def _create_group(self, layout, key, scrollable=False):
        group = QGroupBox()
        self.groups[key] = group
        if scrollable:
            scroll = QScrollArea()
            scroll.setWidget(group)
            scroll.setWidgetResizable(True)
            layout.addWidget(scroll)
            return QVBoxLayout(group)
        else:
            layout.addWidget(group)
            return QFormLayout(group)

    def _create_project_analysis_tab(self):
        layout = self._create_tab("tab_project")
        pj_l = self._create_group(layout, "project_group")
        self.inputs['title'] = QLineEdit(
            DEFAULT_CONFIG["project_info"]["title"])
        self.labels['project_title_label'] = QLabel()
        pj_l.addRow(self.labels['project_title_label'], self.inputs['title'])
        an_l = self._create_group(layout, "analysis_options_group")
        an_opts = DEFAULT_CONFIG["analysis_options"]
        self.inputs['is_seismic'] = QCheckBox()
        self.inputs['is_seismic'].setChecked(an_opts["is_seismic"])
        self.inputs['is_seismic'].stateChanged.connect(
            self._toggle_seismic_inputs)
        self.inputs['kh'] = QDoubleSpinBox(
            decimals=3, maximum=1.0, value=an_opts["kh"])
        self.inputs['kv'] = QDoubleSpinBox(
            decimals=3, maximum=1.0, value=an_opts["kv"])
        for w in [self.inputs['kh'], self.inputs['kv']]:
            w.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.labels['kh_label'], self.labels['kv_label'] = QLabel(), QLabel()
        an_l.addRow(self.inputs['is_seismic'])
        an_l.addRow(self.labels['kh_label'], self.inputs['kh'])
        an_l.addRow(self.labels['kv_label'], self.inputs['kv'])
        self.inputs['deflection_check_code'] = QComboBox()
        self.inputs['deflection_check_code'].addItems(
            DEFAULT_CONFIG["deflection_codes"].keys())
        self.inputs['deflection_check_code'].setCurrentText(
            an_opts["deflection_check_code"])
        self.labels['deflection_check_label'] = QLabel()
        an_l.addRow(self.labels['deflection_check_label'],
                    self.inputs['deflection_check_code'])
        self._toggle_seismic_inputs()
        layout.addStretch()

    def _create_soil_tab(self):
        layout = self._create_tab("tab_soil")
        self.soil_layout = self._create_group(
            layout, "soil_profile_group", scrollable=True)
        self.add_soil_button = QPushButton()
        self.add_soil_button.setIcon(QIcon(str(ICON_ROOT / "plus-circle.svg")))
        self.add_soil_button.clicked.connect(self._add_soil_layer_input)
        for i, ld in enumerate(DEFAULT_CONFIG["soil_profile"]):
            self._add_soil_layer_input(ld, i == 0)
        self.soil_layout.addWidget(self.add_soil_button)
        self.soil_layout.addStretch(1)

    def _create_anchors_tab(self):
        layout = self._create_tab("tab_anchors")
        self.anchor_layout = self._create_group(
            layout, "anchor_levels_group", scrollable=True)
        self.add_anchor_button = QPushButton()
        self.add_anchor_button.setIcon(QIcon(str(ICON_ROOT / "plus-circle.svg")))
        self.add_anchor_button.clicked.connect(self._add_anchor_input)
        for depth in DEFAULT_CONFIG["analysis_options"].get("anchor_depths", []):
            self._add_anchor_input(depth)
        self.anchor_layout.addWidget(self.add_anchor_button)
        self.anchor_layout.addStretch(1)

    def _create_structure_geometry_tab(self):
        layout = self._create_tab("tab_structure")
        st_l = self._create_group(layout, "structural_props_group")
        st_props = DEFAULT_CONFIG["structural_properties"]
        self.inputs['manufacturer'] = QComboBox()
        self.inputs['section_model'] = QComboBox()
        self.labels['manufacturer_label'], self.labels['section_model_label'] = QLabel(
        ), QLabel()
        st_l.addRow(self.labels['manufacturer_label'],
                    self.inputs['manufacturer'])
        st_l.addRow(self.labels['section_model_label'],
                    self.inputs['section_model'])
        self.inputs['manufacturer'].addItems(
            DEFAULT_CONFIG["section_database"].keys())
        self.inputs['manufacturer'].setCurrentText(
            st_props["selected_manufacturer"])
        self.inputs['manufacturer'].currentTextChanged.connect(
            self._update_section_models)
        self._update_section_models(st_props["selected_manufacturer"])
        self.inputs['section_model'].setCurrentText(
            st_props["selected_section_model"])
        self.inputs['steel_grade'] = QComboBox()
        self.inputs['steel_grade'].addItems(st_props["steel_grades"].keys())
        self.inputs['steel_grade'].setCurrentText(
            st_props["selected_steel_grade"])
        self.labels['steel_grade_label'] = QLabel()
        st_l.addRow(self.labels['steel_grade_label'],
                    self.inputs['steel_grade'])
        ge_l = self._create_group(layout, "geometry_group")
        geom = DEFAULT_CONFIG["geometry"]
        for key, val, label_key in [
            ('excavation_depth_H',
             geom["excavation_depth_H"],
             'excavation_depth_label'),
            ('backfill_slope_beta',
             geom["backfill_slope_beta"],
             'backfill_slope_label'),
            ('dredge_line_slope_alpha',
             geom["dredge_line_slope_alpha"],
             'dredge_line_slope_label'),
            ('wall_friction_delta',
             geom["wall_friction_delta"],
             'wall_friction_label')]:
            widget = QDoubleSpinBox(decimals=2, maximum=100.0, value=val)
            widget.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
            self.inputs[key] = widget
            self.labels[label_key] = QLabel()
            ge_l.addRow(self.labels[label_key], self.inputs[key])
        layout.addStretch()

    def _update_section_models(self, manufacturer):
        self.inputs['section_model'].clear()
        models = [s['model']
                  for s in DEFAULT_CONFIG['section_database'].get(manufacturer, [])]
        self.inputs['section_model'].addItems(models)

    def _create_loads_tab(self):
        layout = self._create_tab("tab_loads")
        lo_l = self._create_group(layout, "loads_group")
        loads = DEFAULT_CONFIG["loads"]
        for key, val, label_key in [
            ('surcharge_load',
             loads["surcharge_load"],
             'surcharge_label'),
            ('water_level_active',
             loads["water_level_active"],
             'active_water_label'),
            ('water_level_passive',
             loads["water_level_passive"],
             'passive_water_label')]:
            widget = QDoubleSpinBox(decimals=2, maximum=1000.0, value=val)
            widget.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
            self.inputs[key] = widget
            self.labels[label_key] = QLabel()
            lo_l.addRow(self.labels[label_key], self.inputs[key])
        run_button_layout = QHBoxLayout()
        self.run_button = QPushButton()
        self.run_button.setFixedHeight(40)
        self.run_button.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.run_button.clicked.connect(self.run_analysis)
        run_button_layout.addStretch()
        run_button_layout.addWidget(self.run_button)
        run_button_layout.addStretch()
        layout.addStretch()
        layout.addLayout(run_button_layout)
        layout.addStretch()

    def _add_anchor_input(self, depth=1.0):
        widget = AnchorInputWidget(
            depth if isinstance(
                depth, (int, float)) else 1.0, TRANSLATIONS[self.current_lang])
        widget.removed.connect(lambda w: w.deleteLater())
        self.anchor_layout.insertWidget(self.anchor_layout.count() - 2, widget)

    def _add_soil_layer_input(self, layer_data=None, is_first_layer=False):
        widget = SoilLayerWidget(
            layer_data if isinstance(layer_data, dict) else {},
            TRANSLATIONS[self.current_lang], is_first_layer)
        widget.removed.connect(lambda w: w.deleteLater())
        self.soil_layout.insertWidget(self.soil_layout.count() - 2, widget)

    def _toggle_seismic_inputs(self):
        is_checked = self.inputs['is_seismic'].isChecked()
        self.inputs['kh'].setEnabled(is_checked)
        self.inputs['kv'].setEnabled(is_checked)

    def _create_output_panel(self):
        self.output_tabs = QTabWidget()
        self.results_text = QPlainTextEdit(readOnly=True)
        self.output_tabs.addTab(self.results_text, "")
        plot_keys = ["net_pressure", "earth_pressure", "water_pressure",
                     "shear", "moment", "rotation", "deflection"]
        for key in plot_keys:
            plot_widget = QWidget()
            plot_layout = QVBoxLayout(plot_widget)
            canvas = MplCanvas(self)
            self.plot_canvases[key] = canvas
            save_button = QPushButton()
            save_button.setIcon(QIcon(str(ICON_ROOT / "save.svg")))
            save_button.clicked.connect(lambda _, k=key: self.save_plot(k))
            save_button.setEnabled(False)
            button_layout = QHBoxLayout()
            button_layout.addStretch(1)
            button_layout.addWidget(save_button)
            plot_layout.addWidget(canvas)
            plot_layout.addLayout(button_layout)
            self.output_tabs.addTab(plot_widget, "")

    def _language_changed(self, index):
        self.current_lang = "en" if index == 0 else "tr" if index == 1 else "de"
        self.update_ui_language()

    def update_ui_language(self):
        lang = TRANSLATIONS[self.current_lang]
        self.setWindowTitle(lang["window_title"])
        self.file_menu.setTitle(lang["file_menu"])
        self.help_menu.setTitle(lang["help_menu"])
        self.about_action.setText(lang["about_action"])
        self.exit_action.setText(lang["exit_action"])
        self.open_project_action.setText(lang["open_project"])
        self.save_project_action.setText(lang["save_project"])
        for key, group in self.groups.items():
            group.setTitle(lang[key])
        for key, label in self.labels.items():
            label.setText(lang[key])
        self.inputs['is_seismic'].setText(lang["seismic_checkbox"])
        self.add_soil_button.setText(lang["add_soil_layer_button"])
        self.add_soil_button.setToolTip(lang["add_soil_layer_button"])
        self.add_anchor_button.setText(lang["add_anchor_button"])
        self.add_anchor_button.setToolTip(lang["add_anchor_button"])
        self.run_button.setText(lang["run_analysis_button"])
        self.output_tabs.setTabText(0, lang["results_summary_tab"])
        if not self.current_analysis:
            self.results_text.setPlainText(lang["results_placeholder"])
        for i in range(self.anchor_layout.count() - 2):
            widget = self.anchor_layout.itemAt(i).widget()
            if isinstance(widget, AnchorInputWidget):
                widget.update_language(lang)
        for i in range(self.soil_layout.count() - 2):
            widget = self.soil_layout.itemAt(i).widget()
            if isinstance(widget, SoilLayerWidget):
                widget.update_language(lang)
        if self.current_analysis:
            self._update_results_text()
            self._update_plots()
        for key, tab in self.input_tabs.items():
            self.input_tabs_widget.setTabText(
                self.input_tabs_widget.indexOf(tab), lang[key])
        self.file_menu.clear()
        self.file_menu.addAction(self.open_project_action)
        self.file_menu.addAction(self.save_project_action)
        self.file_menu.addSeparator()
        self.save_plot_actions.clear()
        plot_keys = ["net_pressure", "earth_pressure", "water_pressure",
                     "shear", "moment", "rotation", "deflection"]
        for i, key in enumerate(plot_keys):
            tab_name_key = f"tab_{key}"
            tab_name = lang.get(tab_name_key, key.replace("_", " ").title())
            self.output_tabs.setTabText(i + 1, tab_name)
            save_button = self.output_tabs.widget(i + 1).findChild(QPushButton)
            save_button.setText(lang["save_plot_button"])
            save_button.setToolTip(lang["save_plot_button"])

            action = QAction(
                QIcon(str(ICON_ROOT / "save.svg")),
                lang["save_plot_action"].format(plot_name=tab_name), self)
            action.triggered.connect(lambda _, k=key: self.save_plot(k))
            action.setEnabled(False)
            self.save_plot_actions[key] = action
            self.file_menu.addAction(action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)

    def run_analysis(self):
        self.current_wall, self.current_analysis = None, None
        for action in self.save_plot_actions.values():
            action.setEnabled(False)
        for i in range(1, self.output_tabs.count()):
            self.output_tabs.widget(i).findChild(QPushButton).setEnabled(False)
        lang = TRANSLATIONS[self.current_lang]
        try:
            config_data = self._get_config_from_ui(for_saving=False)
            self.results_text.setPlainText(
                lang["running_analysis"])
            QApplication.processEvents()
            self.current_wall = RetainingWall(config_data)
            self.current_analysis = AnalysisEngine(self.current_wall)
            self.current_analysis.run()
            self._update_results_text()
            self._update_plots()
            for action in self.save_plot_actions.values():
                action.setEnabled(True)
            for i in range(1, self.output_tabs.count()):
                self.output_tabs.widget(
                    i).findChild(QPushButton).setEnabled(True)
            self.output_tabs.setCurrentIndex(1)
            QMessageBox.information(
                self, lang["analysis_complete"], lang["analysis_complete"])
        except Exception as e:
            error_msg = lang["error_message"].format(type=type(e).__name__, e=e)
            QMessageBox.critical(self, lang["error_title"], error_msg)
            self.results_text.setPlainText(error_msg)
            for canvas in self.plot_canvases.values():
                canvas.figure.clear()
                canvas.draw()
            plt.close('all')

    def _get_config_from_ui(self, for_saving=True) -> dict:
        data = {}
        if for_saving:
            data['version'] = '0.1'
        data['project_info'] = {'title': self.inputs['title'].text()}
        data['soil_profile'] = [self.soil_layout.itemAt(
            i).widget().get_data() for i in range(self.soil_layout.count() - 2)]
        data['analysis_options'] = {
            "anchor_depths": [
                self.anchor_layout.itemAt(i).widget().get_depth() for i in range(
                    self.anchor_layout.count() - 2)],
            "is_seismic": self.inputs['is_seismic'].isChecked(),
            "kh": self.inputs['kh'].value(),
            "kv": self.inputs['kv'].value(),
            "deflection_check_code": self.inputs['deflection_check_code'].currentText()}
        data['structural_properties'] = {
            'selected_manufacturer': self.inputs['manufacturer'].currentText(),
            'selected_section_model': self.inputs['section_model'].currentText(),
            'selected_steel_grade': self.inputs['steel_grade'].currentText()}
        data['geometry'] = {
            k: self.inputs[k].value() for k in [
                'excavation_depth_H',
                'backfill_slope_beta',
                'dredge_line_slope_alpha',
                'wall_friction_delta']}
        data['loads'] = {
            k: self.inputs[k].value() for k in [
                'surcharge_load',
                'water_level_active',
                'water_level_passive']}
        if not for_saving:
            full_config = copy.deepcopy(DEFAULT_CONFIG)
            for key, value in data.items():
                if isinstance(value, dict) and key in full_config:
                    full_config[key].update(value)
                else:
                    full_config[key] = value
            return full_config
        return data

    def _set_config_to_ui(self, data: dict):
        for i in range(self.anchor_layout.count() - 2):
            item = self.anchor_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        for i in range(self.soil_layout.count() - 2):
            item = self.soil_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        self.inputs['title'].setText(
            data.get('project_info', {}).get('title', ''))
        opts = data.get('analysis_options', {})
        self.inputs['is_seismic'].setChecked(opts.get('is_seismic', False))
        self.inputs['kh'].setValue(opts.get('kh', 0.0))
        self.inputs['kv'].setValue(opts.get('kv', 0.0))
        self.inputs['deflection_check_code'].setCurrentText(
            opts.get('deflection_check_code', 'No Check'))
        struct = data.get('structural_properties', {})
        self.inputs['manufacturer'].setCurrentText(
            struct.get('selected_manufacturer', ''))
        self._update_section_models(struct.get('selected_manufacturer', ''))
        self.inputs['section_model'].setCurrentText(
            struct.get('selected_section_model', ''))
        self.inputs['steel_grade'].setCurrentText(
            struct.get('selected_steel_grade', ''))
        for key, value in data.get('geometry', {}).items():
            self.inputs[key].setValue(value)
        for key, value in data.get('loads', {}).items():
            self.inputs[key].setValue(value)
        for i, layer_data in enumerate(data.get('soil_profile', [])):
            self._add_soil_layer_input(layer_data, is_first_layer=(i == 0))
        for depth in data.get('analysis_options', {}).get('anchor_depths', []):
            self._add_anchor_input(depth)

    def save_project(self):
        lang = TRANSLATIONS[self.current_lang]
        file_path, _ = QFileDialog.getSaveFileName(
            self, lang["save_project"], "",
            "Sheet Pile Wall Analysis (*.spwa)")
        if not file_path:
            return
        data_to_save = self._get_config_from_ui(for_saving=True)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4)
            QMessageBox.information(
                self, lang["save_success_title"], lang["save_success_message"].format(
                    path=file_path))
        except Exception as e:
            QMessageBox.critical(
                self, lang["error_title"], lang["save_error_message"].format(
                    e=e))

    def open_project(self):
        lang = TRANSLATIONS[self.current_lang]
        file_path, _ = QFileDialog.getOpenFileName(
            self, lang["open_project"], "",
            "Sheet Pile Wall Analysis (*.spwa)")
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._set_config_to_ui(data)
        except Exception as e:
            QMessageBox.critical(
                self, lang["error_title"], lang["error_message"].format(
                    type=type(e).__name__, e=e))

    def _update_results_text(self):
        if not self.current_analysis:
            return
        res, wall, lang = self.current_analysis.results, self.current_wall, TRANSLATIONS[
            self.current_lang]
        text_lines = [
            lang["design_results_title"],
            lang["selected_section"].format(
                model=wall.selected_section_model,
                grade=wall.selected_steel_grade),
            "-" * 50,
            lang["req_embedment"].format(val=self.current_analysis.d_required),
            lang["design_embedment"].format(
                val=self.current_analysis.d_design),
            lang["total_length"].format(
                val=wall.h + self.current_analysis.d_design),
            lang["anchor_forces_title"]
        ]
        if not self.current_analysis.is_cantilever:
            for depth, force in sorted(
                    self.current_analysis.t_anchors.items()):
                text_lines.append(
                    lang["anchor_force_line"].format(
                        depth=depth, force=force))
        else:
            text_lines.append(lang["no_anchors"])
        text_lines.extend([
            lang["summary_of_results_title"],
            lang["summary_pressure"].format(
                p_min=res['p_min'], p_max=res['p_max']),
            lang["summary_shear"].format(
                v_min=res['v_min'], v_max=res['v_max']),
            lang["summary_moment"].format(
                m_min=res['m_min'], m_max=res['m_max']),
            lang["summary_rotation"].format(
                rot_min=res['rot_min'], rot_max=res['rot_max']),
            lang["summary_deflection"].format(
                d_min=np.min(res['deflection']) * 1000,
                d_max=np.max(res['deflection']) * 1000),
            lang["stress_check_title"],
            lang["max_abs_moment"].format(val=res['m_max_abs']),
            lang["actual_stress"].format(val=res['actual_stress'] / 1000),
            lang["allowable_stress"].format(val=wall.f_allowable / 1000),
            lang["status"].format(status=res['stress_check_status'])
        ])
        selected_code = wall.config['analysis_options']['deflection_check_code']
        if res['deflection_check_status'] != "N/A":
            text_lines.extend([
                lang["deflection_check_title"].format(code=selected_code),
                lang["actual_deflection"].format(
                    val=res['actual_max_deflection']),
                lang["allowable_deflection"].format(
                    val=res['allowable_deflection']),
                lang["status"].format(status=res['deflection_check_status'])
            ])
        self.results_text.setPlainText("\n".join(text_lines))

    def _update_plots(self):
        """
        Updates all plot canvases by clearing them and redrawing with new data.
        This uses the object-oriented approach for embedding Matplotlib.
        """
        if not self.current_wall or not self.current_analysis:
            return
            
        plotter = Plotter(
            self.current_wall,
            self.current_analysis,
            TRANSLATIONS[self.current_lang])
            
        for key, canvas in self.plot_canvases.items():
            fig = canvas.figure
            fig.clear()
                        
            plotter.setup_plot(key, figure=fig)
                        
            canvas.draw()

    def save_plot(self, plot_key: str):
        lang = TRANSLATIONS[self.current_lang]
        canvas = self.plot_canvases.get(plot_key)
        if not (canvas and hasattr(
                canvas, 'figure') and canvas.figure.get_axes()):
            QMessageBox.warning(
                self, lang["warning_title"], lang["no_plot_warning"])
            return
        tab_name = lang.get(
            f"tab_{plot_key}",
            plot_key.replace(
                "_", " ").title())
        action_text = lang["save_plot_action"].format(plot_name=tab_name)
        file_path, _ = QFileDialog.getSaveFileName(
            self, action_text, "", "PNG (*.png);;JPEG (*.jpg *.jpeg);;PDF (*.pdf)")
        if not file_path:
            return
        try:
            canvas.figure.savefig(file_path, dpi=300, bbox_inches='tight')
            QMessageBox.information(
                self, lang["save_success_title"],
                lang["save_success_message"].format(path=file_path))
        except Exception as e:
            QMessageBox.critical(
                self, lang["error_title"], lang["save_error_message"].format(e=e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

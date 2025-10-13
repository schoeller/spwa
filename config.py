"""
Configuration file for the Sheet Pile Wall Analysis Tool.

This file contains default parameters, constants, and loads external data
like the section database and language translations.
"""

import json
from pathlib import Path

# --- Constants ---
DATABASE_FILE = Path(__file__).parent / "section_database.json"
MM_PER_M = 1000.0  
NUM_PLOT_POINTS = 500  


try:
    with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
        SECTION_DATABASE = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Error loading section database: {e}")
    SECTION_DATABASE = {}


DEFAULT_CONFIG = {
    "project_info": {
        "title": "Project: Multi-Anchor Quay Wall",
        "analyst": "Python Analysis Script",
    },
    "analysis_options": {
        "anchor_depths": [1.5, 4.0],
        "is_seismic": True,
        "kh": 0.1,
        "kv": 0.0,
        "deflection_check_code": "FHWA (H/120)",
    },
    "deflection_codes": {
        "No Check": None,
        "FHWA (H/120)": 120,
        "BS 8002 (H/100)": 100,
        "NAVFAC DM-7.2 (H/240)": 240,
    },
    "structural_properties": {
        "youngs_modulus_E": 210e6,  
        "selected_manufacturer": "Nucor Skyline",
        "selected_section_model": "NZ 26",
        "selected_steel_grade": "S355",
        "steel_grades": {
            "S240GP": 240000, "S270GP": 270000, "S355": 355000,
            "S420": 420000, "S430GP": 430000, "S460AP": 460000
        },
    },
    "section_database": SECTION_DATABASE,
    "geometry": {
        "excavation_depth_H": 8.0,
        "backfill_slope_beta": 0.0,
        "dredge_line_slope_alpha": 0.0,
        "wall_friction_delta": 20.0,
    },
    "loads": {
        "surcharge_load": 15.0,
        "water_level_active": 4.0,
        "water_level_passive": 7.0,
    },
    "factors": {
        "FS_cohesion": 1.25,
        "FS_friction_angle": 1.25,
        "FS_bending": 1.5,
        "embedment_increase_factor": 1.2,
        "rounding_increment": 0.5,
    },
    "constants": {
        "gamma_water": 9.81
    },
    "soil_profile": [
        {
            "name": "Sloped Sandy Gravel",
            "thickness": 25.0,
            "gamma": 19.5,
            "gamma_sat": 21.0,
            "phi": 38,
            "cohesion": 0
        }
    ],
}

TRANSLATIONS = {
    "en": {
        "window_title": "Sheet Pile Wall Analysis v0.1", "file_menu": "&File",
        "help_menu": "&Help", "about_action": "&About",
        "about_title": "About Sheet Pile Wall Analysis",
        "about_text": "<h3>Sheet Pile Wall Analysis v0.1</h3>"
                      "<p>This application performs geotechnical analysis of sheet pile walls "
                      "using the free-earth support method for both cantilever and multi-anchored systems.</p>"
                      "<p>Developed using Python, PyQt6, and Matplotlib.</p>"
                      "<p><b>Developer:</b> Hasan Deniz Altuntaş<br>© 2025 Hasan Deniz Altuntaş</p>",
        "open_project": "&Open Project...", "save_project": "&Save Project As...",
        "exit_action": "E&xit", "lang_label": "Language:",
        "project_group": "Project Information",
        "project_title_label": "Project Title:",
        "analysis_options_group": "Analysis Options",
        "seismic_checkbox": "Activate Seismic Analysis",
        "kh_label": "Horizontal Seismic Coeff. (kh):",
        "kv_label": "Vertical Seismic Coeff. (kv):",
        "deflection_check_label": "Deflection Code:",
        "soil_profile_group": "Soil Profile",
        "add_soil_layer_button": "Add Soil Layer",
        "anchor_levels_group": "Anchor Levels",
        "add_anchor_button": "Add Anchor",
        "structural_props_group": "Structural Properties",
        "section_model_label": "Section Model:",
        "manufacturer_label": "Manufacturer:",
        "steel_grade_label": "Steel Grade:", "geometry_group": "Geometry",
        "excavation_depth_label": "Excavation Depth H (m):",
        "backfill_slope_label": "Backfill Slope β (°):",
        "dredge_line_slope_label": "Dredge Line Slope α (°):",
        "wall_friction_label": "Wall Friction Angle δ (°):",
        "loads_group": "Loads and Water", "surcharge_label": "Surcharge Load (kPa):",
        "active_water_label": "Active Water Level (m):",
        "passive_water_label": "Passive Water Level (m):",
        "run_analysis_button": "RUN ANALYSIS",
        "results_summary_tab": "Results Summary",
        "save_plot_button": "Save Plot",
        "results_placeholder": "Analysis results will be displayed here...",
        "running_analysis": "Running analysis, please wait...",
        "analysis_complete": "Analysis completed successfully.",
        "error_title": "Error", "error_message": "An error occurred:\n\n{type}: {e}",
        "warning_title": "Warning",
        "no_plot_warning": "There is no plot to save. Please run an analysis first.",
        "save_success_title": "Success",
        "save_success_message": "Plot successfully saved to:\n{path}",
        "save_error_message": "An error occurred while saving the plot:\n{e}",
        "layer_name": "Layer Name:", "thickness": "Thickness (m):",
        "unit_weight": "Unit Weight (kN/m³):",
        "sat_unit_weight": "Saturated Unit W. (kN/m³):",
        "friction_angle": "Friction Angle (°):", "cohesion": "Cohesion (kPa):",
        "remove_layer": "Remove This Layer", "depth": "  Depth (m):",
        "remove": "Remove", "design_results_title": "--- DESIGN RESULTS ---",
        "selected_section": "Selected Section: {model} ({grade})",
        "req_embedment": "Theoretical Required Embedment (D_req): {val:.2f} m",
        "design_embedment": "Design Embedment Depth (D_design):     {val:.2f} m",
        "total_length": "Total Wall Length (L_total):          {val:.2f} m",
        "anchor_forces_title": "\n--- ANCHOR FORCES ---",
        "anchor_force_line": "  Depth {depth:.2f} m: {force:.2f} kN/m",
        "no_anchors": "  No anchors (Cantilever Wall).",
        "summary_of_results_title": "\n--- SUMMARY OF RESULTS ---",
        "summary_pressure": "Net Pressure:      Min={p_min:.2f}, Max={p_max:.2f} kPa",
        "summary_shear": "Shear Force:       Min={v_min:.2f}, Max={v_max:.2f} kN/m",
        "summary_moment": "Bending Moment:    Min={m_min:.2f}, Max={m_max:.2f} kNm/m",
        "summary_rotation": "Rotation:          Min={rot_min:.4f}, Max={rot_max:.4f} rad",
        "summary_deflection": "Deflection (mm):   Min={d_min:.2f}, Max={d_max:.2f} mm",
        "stress_check_title": "\n--- STRESS CHECK ---",
        "max_abs_moment": "Max. Absolute Moment: {val:.2f} kNm/m",
        "actual_stress": "Actual Bending Stress (σ_actual):   {val:.1f} MPa",
        "allowable_stress": "Allowable Bending Stress (f_allowable): {val:.1f} MPa",
        "status": "STATUS: {status}",
        "deflection_check_title": "\n--- DEFLECTION CHECK ({code}) ---",
        "actual_deflection": "Actual Max. Deflection (Δ_actual):   {val:.1f} mm",
        "allowable_deflection": "Allowable Deflection (Δ_allowable): {val:.1f} mm",
        "save_plot_action": "Save {plot_name} Plot...",
        "tab_net_pressure": "Net Pressure", "tab_earth_pressure": "Earth Pressure",
        "tab_water_pressure": "Water Pressure", "tab_shear": "Shear Force",
        "tab_moment": "Bending Moment", "tab_rotation": "Rotation",
        "tab_deflection": "Deflection", "anchored_wall": "Anchored Wall",
        "cantilever_wall": "Cantilever Wall", "seismic": "Seismic",
        "static": "Static", "section": "Section",
        "schematic_title": "Problem Schematic", "depth_m": "Depth (m)",
        "water_active": "Water (Active)", "water_passive": "Water (Passive)",
        "dredge_line": "Dredge Line", "earth_active": "Earth (Active)",
        "earth_passive": "Earth (Passive)", "p_max": "P Max", "p_min": "P Min",
        "v_max": "V Max", "v_min": "V Min", "m_max": "M Max", "m_min": "M Min",
        "max_abs_rotation": "Max Abs Rotation", "max_deflection": "Max Deflection",
        "tab_project": "Project & Analysis", "tab_soil": "Soil Profile",
        "tab_anchors": "Anchor Levels", "tab_structure": "Structure & Geometry",
        "tab_loads": "Loads"
    },
    "tr": {
        "window_title": "Palplanş Duvar Analizi v0.1", "file_menu": "&Dosya",
        "help_menu": "&Yardım", "about_action": "&Hakkında",
        "about_title": "Palplanş Duvar Analizi Hakkında",
        "about_text": "<h3>Palplanş Duvar Analizi v0.1</h3>"
                      "<p>Bu uygulama, konsol ve çok ankrajlı sistemler için serbest zemin desteği yöntemini "
                      "kullanarak palplanş duvarlarının geoteknik analizini gerçekleştirir.</p>"
                      "<p>Python, PyQt6 ve Matplotlib kullanılarak geliştirilmiştir.</p>"
                      "<p><b>Geliştirici:</b> Hasan Deniz Altuntaş<br>© 2025 Hasan Deniz Altuntaş</p>",
        "open_project": "&Proje Aç...", "save_project": "Projeyi &Farklı Kaydet...",
        "exit_action": "Çı&kış", "lang_label": "Dil:",
        "project_group": "Proje Bilgileri", "project_title_label": "Proje Başlığı:",
        "analysis_options_group": "Analiz Seçenekleri",
        "seismic_checkbox": "Sismik Analizi Aktive Et",
        "kh_label": "Yatay Sismik Katsayı (kh):",
        "kv_label": "Düşey Sismik Katsayı (kv):",
        "deflection_check_label": "Deplasman Kodu:",
        "soil_profile_group": "Zemin Profili",
        "add_soil_layer_button": "Zemin Tabakası Ekle",
        "anchor_levels_group": "Ankraj Seviyeleri",
        "add_anchor_button": "Ankraj Ekle",
        "structural_props_group": "Yapısal Özellikler",
        "section_model_label": "Kesit Modeli:",
        "manufacturer_label": "Üretici:", "steel_grade_label": "Çelik Sınıfı:",
        "geometry_group": "Geometri",
        "excavation_depth_label": "Kazı Derinliği H (m):",
        "backfill_slope_label": "Dolgu Şev Açısı β (°):",
        "dredge_line_slope_label": "Tarama Hattı Şev Açısı α (°):",
        "wall_friction_label": "Duvar Sürtünme Açısı δ (°):",
        "loads_group": "Yükler ve Su", "surcharge_label": "Sürşarj Yükü (kPa):",
        "active_water_label": "Aktif Su Seviyesi (m):",
        "passive_water_label": "Pasif Su Seviyesi (m):",
        "run_analysis_button": "ANALİZİ ÇALIŞTIR",
        "results_summary_tab": "Sonuç Özeti",
        "save_plot_button": "Grafiği Kaydet",
        "results_placeholder": "Analiz sonuçları burada gösterilecektir...",
        "running_analysis": "Analiz çalıştırılıyor, lütfen bekleyin...",
        "analysis_complete": "Analiz başarıyla tamamlandı.",
        "error_title": "Hata", "error_message": "Bir hata oluştu:\n\n{type}: {e}",
        "warning_title": "Uyarı",
        "no_plot_warning": "Kaydedilecek bir grafik bulunmuyor. Lütfen önce analiz çalıştırın.",
        "save_success_title": "Başarılı",
        "save_success_message": "Grafik başarıyla kaydedildi:\n{path}",
        "save_error_message": "Grafik kaydedilirken bir hata oluştu:\n{e}",
        "layer_name": "Tabaka Adı:", "thickness": "Kalınlık (m):",
        "unit_weight": "Birim Hacim Ağırlığı (kN/m³):",
        "sat_unit_weight": "Doygun Birim Hacim Ağ. (kN/m³):",
        "friction_angle": "İçsel Sürtünme Açısı (°):",
        "cohesion": "Kohezyon (kPa):", "remove_layer": "Bu Tabakayı Kaldır",
        "depth": "  Derinlik (m):", "remove": "Kaldır",
        "design_results_title": "--- TASARIM SONUÇLARI ---",
        "selected_section": "Seçilen Kesit: {model} ({grade})",
        "req_embedment": "Teorik Gerekli Gömülme Derinliği (D_req): {val:.2f} m",
        "design_embedment": "Tasarım Gömülme Derinliği (D_design):     {val:.2f} m",
        "total_length": "Toplam Duvar Uzunluğu (L_total):          {val:.2f} m",
        "anchor_forces_title": "\n--- ANKRAJ KUVVETLERİ ---",
        "anchor_force_line": "  Derinlik {depth:.2f} m: {force:.2f} kN/m",
        "no_anchors": "  Ankraj yok (Konsol Duvar).",
        "summary_of_results_title": "\n--- SONUÇLARIN ÖZETİ ---",
        "summary_pressure": "Net Basınç:        Min={p_min:.2f}, Maks={p_max:.2f} kPa",
        "summary_shear": "Kesme Kuvveti:     Min={v_min:.2f}, Maks={v_max:.2f} kN/m",
        "summary_moment": "Eğilme Momenti:    Min={m_min:.2f}, Maks={m_max:.2f} kNm/m",
        "summary_rotation": "Dönme:             Min={rot_min:.4f}, Maks={rot_max:.4f} rad",
        "summary_deflection": "Deplasman (mm):    Min={d_min:.2f}, Maks={d_max:.2f} mm",
        "stress_check_title": "\n--- GERİLME KONTROLÜ ---",
        "max_abs_moment": "Maksimum Mutlak Moment: {val:.2f} kNm/m",
        "actual_stress": "Oluşan Gerilme (σ_actual):   {val:.1f} MPa",
        "allowable_stress": "İzin Verilen Gerilme (f_allowable): {val:.1f} MPa",
        "status": "DURUM: {status}",
        "deflection_check_title": "\n--- DEPLASMAN KONTROLÜ ({code}) ---",
        "actual_deflection": "Oluşan Maks. Deplasman (Δ_actual):   {val:.1f} mm",
        "allowable_deflection": "İzin Verilen Deplasman (Δ_allowable): {val:.1f} mm",
        "save_plot_action": "{plot_name} Grafiğini Kaydet...",
        "tab_net_pressure": "Net Basınç", "tab_earth_pressure": "Zemin Basıncı",
        "tab_water_pressure": "Su Basıncı", "tab_shear": "Kesme Kuvveti",
        "tab_moment": "Eğilme Momenti", "tab_rotation": "Dönme",
        "tab_deflection": "Deplasman", "anchored_wall": "Ankrajlı Duvar",
        "cantilever_wall": "Konsol Duvar", "seismic": "Sismik",
        "static": "Statik", "section": "Kesit",
        "schematic_title": "Problem Şeması", "depth_m": "Derinlik (m)",
        "water_active": "Su (Aktif)", "water_passive": "Su (Pasif)",
        "dredge_line": "Tarama Hattı", "earth_active": "Zemin (Aktif)",
        "earth_passive": "Zemin (Pasif)", "p_max": "P Maks", "p_min": "P Min",
        "v_max": "V Maks", "v_min": "V Min", "m_max": "M Maks", "m_min": "M Min",
        "max_abs_rotation": "Maks Mutlak Dönme",
        "max_deflection": "Maks Deplasman",
        "tab_project": "Proje & Analiz", "tab_soil": "Zemin Profili",
        "tab_anchors": "Ankraj Seviyeleri",
        "tab_structure": "Yapısal & Geometri", "tab_loads": "Yükler"
    }
}

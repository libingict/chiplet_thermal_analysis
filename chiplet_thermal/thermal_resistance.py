# chiplet_thermal/thermal_resistance.py
import numpy as np
from dataclasses import dataclass

from . import constants as C


@dataclass
class ChipletThermal:
    """
    单 Chiplet 内部热阻（结到芯片表面，不含 TIM）
    公式：R_chip = R_DRAM + R_HB1 + R_Basic + R_HB2 + R_Logic
    """
    theta_jc: float = 0.12           # 当 use_physical=False 时直接使用
    use_physical: bool = False

    # ----- DRAM 参数 -----
    num_dram_layers: int = C.N_DRAM_LAYERS
    dram_thickness: float = C.DRAM_THICKNESS

    # ----- Basic Die 参数 -----
    basic_thickness: float = C.BASIC_THICKNESS

    # ----- GPU Logic 参数 -----
    logic_thickness: float = C.LOGIC_THICKNESS
    hotspot_area_ratio: float = C.HOTSPOT_AREA_RATIO
    use_spreading: bool = C.USE_SPREADING

    # ----- 通用材料参数 -----
    k_si: float = C.SI_K
    chiplet_area: float = 200e-6  # 占位，由外部按面积更新

    # ----- TIM 参数 -----
    tim_thickness: float = C.TIM_THICKNESS
    k_tim: float = C.TIM_K

    hb_thermal_density: float = C.HB_THERMAL_RES_DENSITY


    def __post_init__(self):
        if self.use_physical:
            self.theta_jc = self.compute_theta_jc()

    def compute_theta_jc(self) -> float:
        return self.compute_theta_jc_for_area(self.chiplet_area)

    def compute_theta_jc_for_area(self, area: float) -> float: #单chiplet面积，单chiplet内部热阻
        """返回 R_θ,chip (K/W) 不含 TIM
                 公式：R_chip = R_DRAM + R_HB1 + R_Basic + R_HB2 + R_Logic
         其中 R_HB1 和 R_HB2 都使用 hb_thermal_density / area 来计算，表示混合键合界面热阻，考虑两个界面
        """

        # DRAM (公式2)
        r_dram = (self.num_dram_layers * self.dram_thickness) / (self.k_si * area)
        # 混合键合 (公式4)，两个界面
        r_hb = self.hb_thermal_density / area
        # Basic Die (公式5)
        r_basic = self.basic_thickness / (self.k_si * area)
        # Logic (公式7)
        r_logic = self.logic_thickness / (self.k_si * area)
        return r_dram + r_hb + r_basic + r_hb + r_logic

    def compute_thermal_details(self, area: float) -> dict: # 返回热阻分解细节，方便分析和展示
        r_dram = (self.num_dram_layers * self.dram_thickness) / (self.k_si * area)
        r_hb = self.hb_thermal_density / area
        r_basic = self.basic_thickness / (self.k_si * area)
        r_logic = self.logic_thickness / (self.k_si * area)
        theta_jc = r_dram + 2 * r_hb + r_basic + r_logic
        return {
            "theta_jc_total": theta_jc,
            "r_dram": r_dram,
            "r_hb": r_hb,
            "r_basic": r_basic,
            "r_logic": r_logic,
        }


@dataclass
class PackageThermal:
    """封装级热阻 (壳‑环境)，支持系统级热耦合因子 η 和中介层热阻"""
    use_physical: bool = False
    theta_ca: float = 0.015               # 直接指定
    h: float = C.H_CONVECTION
    fin_area_ratio: float = C.FIN_AREA_RATIO
    fin_efficiency: float = C.FIN_EFFICIENCY
    tim_thickness: float = C.TIM_THICKNESS
    k_tim: float = C.TIM_K
    use_interposer: bool = C.USE_INTERPOSER_THERMAL
    interposer_thickness: float = C.INTERPOSER_THICKNESS
    interposer_k: float = C.INTERPOSER_K
    thermal_coupling_factor: float = C.THERMAL_COUPLING_FACTOR


    def compute_theta_ca(self, total_chip_area_m2: float) -> float:
        """返回 R_TIM + R_HS + R_interposer (不含耦合因子)"""
        if not self.use_physical:
            return self.theta_ca
        # TIM
        r_tim = self.tim_thickness / (self.k_tim * total_chip_area_m2)
        # 散热器
        a_fins = self.fin_area_ratio * total_chip_area_m2
        r_hs = 1.0 / (self.h * a_fins * self.fin_efficiency)
        # 中介层
        r_interposer = 0.0
        if self.use_interposer:
            r_interposer = self.interposer_thickness / (self.interposer_k * total_chip_area_m2)
        return r_tim + r_hs + r_interposer
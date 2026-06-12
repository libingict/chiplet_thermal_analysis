# chiplet_thermal/models.py
from dataclasses import dataclass, field
from typing import List, Optional, Union

from . import constants as C
from .thermal_resistance import ChipletThermal, PackageThermal


@dataclass
class ProcessNode:
    """工艺节点能效参数"""
    name: str
    fp16_efficiency: float  # FP16 能效 (TFLOPS/W)，仅针对 GPU 逻辑
    description: str = ""


@dataclass
class ChipletConfig:
    """单 Chiplet 配置（热、功耗、工艺）；默认值与 chiplet_thermal.constants 对齐。"""
    num_chiplets: int
    target_total_fp16: float  # 总算力 (TFLOPS)，由用户指定，平均分配到每个 chiplet
    process: ProcessNode

    # 面积模型参数
    transistor_density: float = C.TRANSISTOR_DENSITY
    util_factor: float = C.UTIL_FACTOR
    arch_efficiency: float = C.ARCH_EFFICIENCY
    n_signal_tsv: int = C.N_SIGNAL_TSV
    n_power_tsv: int = C.N_POWER_TSV
    area_signal_via_um2: float = C.AREA_SIGNAL_VIA_UM2
    area_power_via_um2: float = C.AREA_POWER_VIA_UM2
    hb_bump_pitch_um: float = C.HB_BUMP_PITCH_UM
    n_total_bumps: int = 0  # 0 则自动 = n_sig + n_pow
    alpha_package: float = C.ALPHA_PACKAGE

    # 功耗 - 逻辑
    alpha_activity: float = C.ALPHA_ACTIVITY
    c_unit_f_per_mm2: float = C.C_UNIT_F_PER_MM2
    vdd: float = C.VDD
    f_clk: float = C.F_CLK
    j_leakage_a_per_mm2: float = C.J_LEAKAGE_A_PER_MM2

    # 功耗 - 内存
    e_bit_pj: float = C.E_BIT_PJ
    bw_per_chiplet_tb_s: float = C.BW_PER_CHIPLET_TB_S
    p_tsv_driver_per_signal: float = C.P_TSV_DRIVER_PER_SIGNAL_W
    num_dram_layers: int = C.N_DRAM_LAYERS
    p_refresh_per_die: float = C.P_REFRESH_PER_DIE_W
    p_leak_per_die: float = C.P_LEAK_PER_DIE_W
    basic_overhead_ratio: float = C.BASIC_OVERHEAD_RATIO
    rate_data_per_tsv_bit_s: float = C.RATE_DATA_PER_TSV_BIT_S

    # 封装损耗
    package_loss_ratio: float = C.PACKAGE_LOSS_RATIO
    interposer_power_total: float = C.INTERPOSER_POWER_TOTAL_W

    # 热环境
    ambient_temp: float = C.AMBIENT_TEMP
    use_hierarchical: bool = False
    chip_thermal: ChipletThermal = field(default_factory=ChipletThermal)
    package_thermal: PackageThermal = field(default_factory=PackageThermal)
    theta_ja: float = C.THETA_JA_SIMPLE



@dataclass
class PowerThermalResult:
    """功耗与热分析结果"""
    num_chiplets: int
    logic_power_per_chiplet: float
    total_power_per_chiplet: float
    total_package_power: float
    junction_temp: Union[float, List[float]]
    case_temp: Optional[float] = None

    chiplet_area_mm2: float = 0.0          # 单 chiplet 面积 (mm²)
    total_chip_area_mm2: float = 0.0       # 所有 chiplet 总面积 (mm²)
    logic_area_mm2: float = 0.0            # 逻辑部分面积 (mm²)
    memory_area_mm2: float = 0.0           # 内存部分面积 (mm²)
    interconnect_area_mm2: float = 0.0     # 互连开销 (mm²)
    tsv_area_mm2: float = 0.0          # TSV 占用面积 (mm²)
    thermal_details: Optional[dict] = None  # 分层热阻分解细节
# chiplet_thermal/constants.py
# 基准：Nvidia H200
H200_FP16_TFLOPS = 1979.0          # FP16 Tensor Core 稠密算力
H200_TDP = 700.0                  # SXM 模块总功耗
HBM_POWER_RATIO = 0.20
H200_MEM_POWER = H200_TDP * HBM_POWER_RATIO
H200_LOGIC_POWER = H200_TDP - H200_MEM_POWER
H200_LOGIC_EFFICIENCY = H200_FP16_TFLOPS / H200_LOGIC_POWER
H200_POWER_DENSITY = 0.86 #W/mm2
H200_F_CLK = 1.8e9 #GHz

# 工艺
DOMESTIC_PROCESS_PENALTY = 1.2 #
# 相对参考逻辑能效，国内工艺惩罚后的等效能效 (TFLOPS/W)
DOMESTIC_5NM_EFF = H200_LOGIC_EFFICIENCY / DOMESTIC_PROCESS_PENALTY
TRANSISTOR_DENSITY = 150.0         # M/mm²
UTIL_FACTOR = 0.4
ARCH_EFFICIENCY = 0.0158           # TFLOPS/M 晶体管
ALPHA_PACKAGE = 1.3

# 面积 - TSV 详细参数
N_SIGNAL_TSV = 1_000_000           # 信号 TSV 数量
N_POWER_TSV = 250_000              # 电源 TSV 数量
AREA_SIGNAL_VIA_UM2 = 10.0         # 单信号 TSV 占用 μm²
AREA_POWER_VIA_UM2 = 40.0          # 单电源 TSV 占用 μm²
HB_BUMP_PITCH_UM = 4.5             # 混合键合焊盘 pitch (μm)
HB_TOTAL_BUMPS = 1_250_000         # 总焊盘数（可自动= N_sig+N_pow）


# 功耗 - 逻辑
LOGIC_POWER_STATIC_FRACTION = 0.2
LOGIC_POWER_DYNAMIC_FRACTION = 0.8
ALPHA_ACTIVITY = 0.2
C_UNIT_F_PER_MM2 = 1.5e-13         # F/mm² -> 150 fF/mm²
VDD = 0.8
F_CLK = 1.6e9                      # 1.6 GHz
J_LEAKAGE_A_PER_MM2 = 0.1          # A/mm² @高温

# 功耗 - 内存
E_BIT_PJ = 2.5e-12                 # 2.5 pJ/bit
BW_PER_CHIPLET_TB_S = 1.2          # TB/s
P_TSV_DRIVER_PER_SIGNAL_W = 1.5e-3 # 1 mW per signal TSV 驱动功耗， 或者1.5mW更保守
RATE_DATA_PER_TSV_BIT_S = 6.4e9      # 每个 TSV 串行比特率 (bit/s)，约 6.4 Gb/s
POWER_TSV_RATIO = 0.5              # 电源 TSV 数量占信号 TSV 的比例
TSV_REDUNDANCY = 4             # TSV 冗余倍数，考虑工艺缺陷和可靠性，通常 2~4 倍
P_REFRESH_PER_DIE_W = 0.4          # 400 mW, DRAM 层刷新功耗
P_LEAK_PER_DIE_W = 0.1             # 100 mW, DRAM 层漏电功耗
BASIC_OVERHEAD_RATIO = 0.03        # Basic Die 额外功耗比例

# 封装
PACKAGE_LOSS_RATIO = 0.08 # 8% 封装损耗
INTERPOSER_POWER_TOTAL_W = 30.0  # 30 W 固定互连功耗（不随芯片数量变化）

# 热环境
AMBIENT_TEMP = 45.0 # °C
THETA_JA_SIMPLE = 0.025 # °C/W，简单模型总热阻

# 热阻默认值（不变）
N_DRAM_LAYERS = 8 # 默认8层DRAM
DRAM_THICKNESS = 50e-6 # 50 μm DRAM 层厚度
DRAM_TSV_DENSITY = 0.03 # 3% DRAM TSV 面积占比
TSV_DIAMETER = 5e-6 #
BASIC_THICKNESS = 30e-6 # 30 μm Basic Die 厚度
BASIC_TSV_DENSITY = 0.0 # Basic Die 无 TSV
LOGIC_THICKNESS = 80e-6 # 80 μm Logic 层厚度
HOTSPOT_AREA_RATIO = 0.2 # 热点面积占比
USE_SPREADING = False # 默认不考虑热点扩散热阻
SI_K = 120.0 # 硅导热系数 W/m·K
CU_K = 385.0 # 铜导热系数 W/m·K

# 混合键合
HYBRID_BOND_MODEL = "simplified"     # 或 "physical"
HB_THERMAL_RES_DENSITY = 1.0e-6      # 1.0 mm²·K/W
CU_COVERAGE = 0.25   # 铜覆盖率
R_CU_INTERFACE_DENSITY = 0.8e-6
R_DIELECTRIC_DENSITY = 3.5e-6
TIM_THICKNESS = 0.1e-3 # 100 μm
TIM_K = 3.0 # TIM 导热系数 W/m·K

# 系统热耦合
# THERMAL_COUPLING_FACTOR = 1.15

# POWER_PER_TSV = 0.1e-6          # W per TSV (0.1 µW)
# USE_TSV_POWER_MODEL = True      # 默认启用动态TSV功耗模型

# # DRAM 层功耗模型（可选用）
# POWER_PER_DRAM_LAYER = 20.0     # W per DRAM layer
# USE_DRAM_LAYER_POWER = False    # 默认仍按 HBM 比例均分总内存功耗

# 散热物理模型默认值
H_CONVECTION = 50.0        # W/m²·K
FIN_AREA_RATIO = 10.0
FIN_EFFICIENCY = 0.8
THERMAL_COUPLING_FACTOR = 1.15
USE_INTERPOSER_THERMAL = False
INTERPOSER_THICKNESS = 2e-4 # 200 μm
INTERPOSER_K = 0.4 # W/m·K, Interposer 导热系数
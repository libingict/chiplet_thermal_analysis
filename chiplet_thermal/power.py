# chiplet_thermal/power.py
from . import constants


def compute_chiplet_power_v2(config, logic_area_mm2):
    """工程化版本：逻辑按 H200 功率密度缩放，内存按 bit 能量与 TSV 驱动估算。"""
    r_stat = constants.LOGIC_POWER_STATIC_FRACTION # 静态功率比例
    r_dyn = constants.LOGIC_POWER_DYNAMIC_FRACTION # 动态功率比例
    p_logic_basic = logic_area_mm2 * constants.H200_POWER_DENSITY # 基础逻辑功率
    p_logic_freq = p_logic_basic * config.f_clk / constants.H200_F_CLK # 频率缩放
    total_logic_power = p_logic_freq * constants.DOMESTIC_PROCESS_PENALTY # 工艺修正
    p_stat_logic = total_logic_power * r_stat
    p_dyn_logic = total_logic_power * r_dyn

    bw_bps = config.bw_per_chiplet_tb_s * 8 * 1e12
    p_dyn_mem = (
        config.e_bit_pj * bw_bps
        + config.n_signal_tsv * config.p_tsv_driver_per_signal
    )
    p_stat_mem = config.num_dram_layers * (config.p_refresh_per_die + config.p_leak_per_die)

    p_basic = config.basic_overhead_ratio * (
        p_dyn_logic + p_stat_logic + p_dyn_mem + p_stat_mem
    )

    p_chiplet = p_dyn_logic + p_stat_logic + p_dyn_mem + p_stat_mem + p_basic
    return p_dyn_logic, p_stat_logic, p_chiplet


def compute_chiplet_power(config, logic_area_mm2):
    c_total = config.c_unit_f_per_mm2 * logic_area_mm2
    p_dyn_logic = config.alpha_activity * c_total * config.vdd**2 * config.f_clk
    i_leak = config.j_leakage_a_per_mm2 * logic_area_mm2
    p_stat_logic = i_leak * config.vdd

    bw_bps = config.bw_per_chiplet_tb_s * 8 * 1e12
    p_dyn_mem = (
        config.e_bit_pj * bw_bps
        + config.n_signal_tsv * config.p_tsv_driver_per_signal
    )
    p_stat_mem = config.num_dram_layers * (config.p_refresh_per_die + config.p_leak_per_die)

    p_basic = config.basic_overhead_ratio * (
        p_dyn_logic + p_stat_logic + p_dyn_mem + p_stat_mem
    )

    p_chiplet = p_dyn_logic + p_stat_logic + p_dyn_mem + p_stat_mem + p_basic
    return p_dyn_logic, p_stat_logic, p_chiplet


def compute_package_power(config, p_chiplet_single):
    base = config.num_chiplets * p_chiplet_single
    return base * (1 + config.package_loss_ratio) + config.interposer_power_total

# chiplet_thermal/scaling_defaults.py
"""Single mapping from analyze_scaling / GUI overrides to module constants."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from . import constants as C


@dataclass(frozen=True)
class ScalingResolved:
    """All numeric inputs for scaling sweep after merging overrides with constants."""

    transistor_density: float
    util_factor: float
    arch_efficiency: float
    n_signal_tsv: int
    n_power_tsv: int
    area_signal_via_um2: float
    area_power_via_um2: float
    hb_bump_pitch_um: float
    n_total_bumps: int
    alpha_package: float
    alpha_activity: float
    c_unit_f_per_mm2: float
    vdd: float
    f_clk: float
    j_leakage_a_per_mm2: float
    e_bit_pj: float
    bw_per_chiplet_tb_s: float
    p_tsv_driver_per_signal: float
    rate_data_per_tsv_bit_s: float
    num_dram_layers: int
    p_refresh_per_die: float
    p_leak_per_die: float
    basic_overhead_ratio: float
    package_loss_ratio: float
    interposer_power_total: float
    ambient_temp: float
    theta_ja: float
    dram_thickness: float
    basic_thickness: float
    logic_thickness: float
    k_si: float
    hb_thermal_res_density: float
    tim_thickness: float
    tim_k: float
    use_physical_package: bool
    fin_area_ratio: float
    fin_efficiency: float
    thermal_coupling_factor: float
    use_interposer_thermal: bool
    interposer_thickness: float
    interposer_k: float
    target_total_fp16: float

    def as_chiplet_config_kwargs(self) -> Dict[str, Any]:
        return {
            "transistor_density": self.transistor_density,
            "util_factor": self.util_factor,
            "arch_efficiency": self.arch_efficiency,
            "n_signal_tsv": self.n_signal_tsv,
            "n_power_tsv": self.n_power_tsv,
            "area_signal_via_um2": self.area_signal_via_um2,
            "area_power_via_um2": self.area_power_via_um2,
            "hb_bump_pitch_um": self.hb_bump_pitch_um,
            "n_total_bumps": self.n_total_bumps,
            "alpha_package": self.alpha_package,
            "alpha_activity": self.alpha_activity,
            "c_unit_f_per_mm2": self.c_unit_f_per_mm2,
            "vdd": self.vdd,
            "f_clk": self.f_clk,
            "j_leakage_a_per_mm2": self.j_leakage_a_per_mm2,
            "e_bit_pj": self.e_bit_pj,
            "bw_per_chiplet_tb_s": self.bw_per_chiplet_tb_s,
            "p_tsv_driver_per_signal": self.p_tsv_driver_per_signal,
            "rate_data_per_tsv_bit_s": self.rate_data_per_tsv_bit_s,
            "num_dram_layers": self.num_dram_layers,
            "p_refresh_per_die": self.p_refresh_per_die,
            "p_leak_per_die": self.p_leak_per_die,
            "basic_overhead_ratio": self.basic_overhead_ratio,
            "package_loss_ratio": self.package_loss_ratio,
            "interposer_power_total": self.interposer_power_total,
            "ambient_temp": self.ambient_temp,
            "theta_ja": self.theta_ja,
        }


def _g(val: Optional[Any], default: Any) -> Any:
    return default if val is None else val


def resolve_scaling_params(
    *,
    transistor_density: Optional[float] = None,
    util_factor: Optional[float] = None,
    arch_efficiency: Optional[float] = None,
    n_signal_tsv: Optional[int] = None,
    n_power_tsv: Optional[int] = None,
    area_signal_via_um2: Optional[float] = None,
    area_power_via_um2: Optional[float] = None,
    hb_bump_pitch_um: Optional[float] = None,
    n_total_bumps: Optional[int] = None,
    alpha_package: Optional[float] = None,
    alpha_activity: Optional[float] = None,
    c_unit_f_per_mm2: Optional[float] = None,
    vdd: Optional[float] = None,
    f_clk: Optional[float] = None,
    j_leakage_a_per_mm2: Optional[float] = None,
    e_bit_pj: Optional[float] = None,
    bw_per_chiplet_tb_s: Optional[float] = None,
    p_tsv_driver_per_signal: Optional[float] = None,
    rate_data_per_tsv_bit_s: Optional[float] = None,
    num_dram_layers: Optional[int] = None,
    p_refresh_per_die: Optional[float] = None,
    p_leak_per_die: Optional[float] = None,
    basic_overhead_ratio: Optional[float] = None,
    package_loss_ratio: Optional[float] = None,
    interposer_power_total: Optional[float] = None,
    ambient_temp: Optional[float] = None,
    theta_ja: Optional[float] = None,
    dram_thickness: Optional[float] = None,
    basic_thickness: Optional[float] = None,
    logic_thickness: Optional[float] = None,
    k_si: Optional[float] = None,
    hb_thermal_res_density: Optional[float] = None,
    tim_thickness: Optional[float] = None,
    tim_k: Optional[float] = None,
    use_physical_package: bool = False,
    fin_area_ratio: Optional[float] = None,
    fin_efficiency: Optional[float] = None,
    thermal_coupling_factor: Optional[float] = None,
    use_interposer_thermal: bool = False,
    interposer_thickness: Optional[float] = None,
    interposer_k: Optional[float] = None,
    target_total_fp16: Optional[float] = None,
) -> ScalingResolved:
    n_bumps = _g(n_total_bumps, 0)
    return ScalingResolved(
        transistor_density=_g(transistor_density, C.TRANSISTOR_DENSITY),
        util_factor=_g(util_factor, C.UTIL_FACTOR),
        arch_efficiency=_g(arch_efficiency, C.ARCH_EFFICIENCY),
        n_signal_tsv=int(_g(n_signal_tsv, C.N_SIGNAL_TSV)),
        n_power_tsv=int(_g(n_power_tsv, C.N_POWER_TSV)),
        area_signal_via_um2=_g(area_signal_via_um2, C.AREA_SIGNAL_VIA_UM2),
        area_power_via_um2=_g(area_power_via_um2, C.AREA_POWER_VIA_UM2),
        hb_bump_pitch_um=_g(hb_bump_pitch_um, C.HB_BUMP_PITCH_UM),
        n_total_bumps=int(n_bumps),
        alpha_package=_g(alpha_package, C.ALPHA_PACKAGE),
        alpha_activity=_g(alpha_activity, C.ALPHA_ACTIVITY),
        c_unit_f_per_mm2=_g(c_unit_f_per_mm2, C.C_UNIT_F_PER_MM2),
        vdd=_g(vdd, C.VDD),
        f_clk=_g(f_clk, C.F_CLK),
        j_leakage_a_per_mm2=_g(j_leakage_a_per_mm2, C.J_LEAKAGE_A_PER_MM2),
        e_bit_pj=_g(e_bit_pj, C.E_BIT_PJ),
        bw_per_chiplet_tb_s=_g(bw_per_chiplet_tb_s, C.BW_PER_CHIPLET_TB_S),
        p_tsv_driver_per_signal=_g(p_tsv_driver_per_signal, C.P_TSV_DRIVER_PER_SIGNAL_W),
        rate_data_per_tsv_bit_s=_g(rate_data_per_tsv_bit_s, C.RATE_DATA_PER_TSV_BIT_S),
        num_dram_layers=int(_g(num_dram_layers, C.N_DRAM_LAYERS)),
        p_refresh_per_die=_g(p_refresh_per_die, C.P_REFRESH_PER_DIE_W),
        p_leak_per_die=_g(p_leak_per_die, C.P_LEAK_PER_DIE_W),
        basic_overhead_ratio=_g(basic_overhead_ratio, C.BASIC_OVERHEAD_RATIO),
        package_loss_ratio=_g(package_loss_ratio, C.PACKAGE_LOSS_RATIO),
        interposer_power_total=_g(interposer_power_total, C.INTERPOSER_POWER_TOTAL_W),
        ambient_temp=_g(ambient_temp, C.AMBIENT_TEMP),
        theta_ja=_g(theta_ja, C.THETA_JA_SIMPLE),
        dram_thickness=_g(dram_thickness, C.DRAM_THICKNESS),
        basic_thickness=_g(basic_thickness, C.BASIC_THICKNESS),
        logic_thickness=_g(logic_thickness, C.LOGIC_THICKNESS),
        k_si=_g(k_si, C.SI_K),
        hb_thermal_res_density=_g(hb_thermal_res_density, C.HB_THERMAL_RES_DENSITY),
        tim_thickness=_g(tim_thickness, C.TIM_THICKNESS),
        tim_k=_g(tim_k, C.TIM_K),
        use_physical_package=use_physical_package,
        fin_area_ratio=_g(fin_area_ratio, C.FIN_AREA_RATIO),
        fin_efficiency=_g(fin_efficiency, C.FIN_EFFICIENCY),
        thermal_coupling_factor=_g(thermal_coupling_factor, C.THERMAL_COUPLING_FACTOR),
        use_interposer_thermal=use_interposer_thermal,
        interposer_thickness=_g(interposer_thickness, C.INTERPOSER_THICKNESS),
        interposer_k=_g(interposer_k, C.INTERPOSER_K),
        target_total_fp16=_g(target_total_fp16, C.H200_FP16_TFLOPS),
    )

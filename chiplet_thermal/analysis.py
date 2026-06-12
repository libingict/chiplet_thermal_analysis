# chiplet_thermal/analysis.py
import numpy as np
import pandas as pd
from typing import List, Optional

from .models import ProcessNode, ChipletConfig, ChipletThermal, PackageThermal
from .analyzer import ThermalPowerAnalyzer
from . import constants as const
from .scaling_defaults import resolve_scaling_params


def analyze_scaling(
    chiplet_counts: List[int],
    use_hierarchical: bool = False,
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
) -> pd.DataFrame:
    p = resolve_scaling_params(
        transistor_density=transistor_density,
        util_factor=util_factor,
        arch_efficiency=arch_efficiency,
        n_signal_tsv=n_signal_tsv,
        n_power_tsv=n_power_tsv,
        area_signal_via_um2=area_signal_via_um2,
        area_power_via_um2=area_power_via_um2,
        hb_bump_pitch_um=hb_bump_pitch_um,
        n_total_bumps=n_total_bumps,
        alpha_package=alpha_package,
        alpha_activity=alpha_activity,
        c_unit_f_per_mm2=c_unit_f_per_mm2,
        vdd=vdd,
        f_clk=f_clk,
        j_leakage_a_per_mm2=j_leakage_a_per_mm2,
        e_bit_pj=e_bit_pj,
        bw_per_chiplet_tb_s=bw_per_chiplet_tb_s,
        p_tsv_driver_per_signal=p_tsv_driver_per_signal,
        rate_data_per_tsv_bit_s=rate_data_per_tsv_bit_s,
        num_dram_layers=num_dram_layers,
        p_refresh_per_die=p_refresh_per_die,
        p_leak_per_die=p_leak_per_die,
        basic_overhead_ratio=basic_overhead_ratio,
        package_loss_ratio=package_loss_ratio,
        interposer_power_total=interposer_power_total,
        ambient_temp=ambient_temp,
        theta_ja=theta_ja,
        dram_thickness=dram_thickness,
        basic_thickness=basic_thickness,
        logic_thickness=logic_thickness,
        k_si=k_si,
        hb_thermal_res_density=hb_thermal_res_density,
        tim_thickness=tim_thickness,
        tim_k=tim_k,
        use_physical_package=use_physical_package,
        fin_area_ratio=fin_area_ratio,
        fin_efficiency=fin_efficiency,
        thermal_coupling_factor=thermal_coupling_factor,
        use_interposer_thermal=use_interposer_thermal,
        interposer_thickness=interposer_thickness,
        interposer_k=interposer_k,
        target_total_fp16=target_total_fp16,
    )

    results = []
    for n in chiplet_counts:
        chip_thermal = ChipletThermal(
            use_physical=True,
            num_dram_layers=p.num_dram_layers,
            dram_thickness=p.dram_thickness,
            basic_thickness=p.basic_thickness,
            logic_thickness=p.logic_thickness,
            k_si=p.k_si,
            hb_thermal_density=p.hb_thermal_res_density,
            tim_thickness=p.tim_thickness,
            k_tim=p.tim_k,
            chiplet_area=100e-6,
        )
        pkg_thermal = PackageThermal(
            use_physical=p.use_physical_package,
            fin_area_ratio=p.fin_area_ratio,
            fin_efficiency=p.fin_efficiency,
            thermal_coupling_factor=p.thermal_coupling_factor,
            use_interposer=p.use_interposer_thermal,
            interposer_thickness=p.interposer_thickness,
            interposer_k=p.interposer_k,
            tim_thickness=p.tim_thickness,
            k_tim=p.tim_k,
        )
        cfg_kw = p.as_chiplet_config_kwargs()
        config = ChipletConfig(
            num_chiplets=n,
            target_total_fp16=p.target_total_fp16,
            process=ProcessNode("config", fp16_efficiency=0.0),
            use_hierarchical=use_hierarchical,
            chip_thermal=chip_thermal,
            package_thermal=pkg_thermal,
            **cfg_kw,
        )
        analyzer = ThermalPowerAnalyzer(config)
        res = analyzer.analyze()

        tj = res.junction_temp
        if isinstance(tj, list):
            tj_str = f"{np.mean(tj):.2f}"
        else:
            tj_str = f"{tj:.2f}"

        results.append({
            "Chiplet数量": n,
            "逻辑面积(mm²)": round(res.logic_area_mm2, 2),
            "单Chiplet面积(mm²)": round(res.chiplet_area_mm2, 2),
            "封装总面积(mm²)": round(res.total_chip_area_mm2, 2),
            "逻辑功耗(W)": round(res.logic_power_per_chiplet, 2),
            "单Chiplet总功耗(W)": round(res.total_power_per_chiplet, 2),
            "封装总功耗(W)": round(res.total_package_power, 2),
            "结温(°C)": tj_str,
        })
    return pd.DataFrame(results)


def custom_analysis(
    num_chiplets: int = 4,
    target_fp16: float = const.H200_FP16_TFLOPS,
    dram_per_chiplet: Optional[float] = None,
    ambient: float = const.AMBIENT_TEMP,
    use_hierarchical: bool = False,
    **kwargs,
):
    """自定义热分析入口函数。"""
    if dram_per_chiplet is None:
        dram_per_chiplet = const.H200_MEM_POWER / num_chiplets
    # dram_per_chiplet 保留供后续内存功耗拆分；当前模型未使用该字段
    _ = dram_per_chiplet
    merged = {
        **kwargs,
        "target_total_fp16": target_fp16,
        "ambient_temp": ambient,
    }
    return analyze_scaling(
        chiplet_counts=[num_chiplets],
        use_hierarchical=use_hierarchical,
        **merged,
    )

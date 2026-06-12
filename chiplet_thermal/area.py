# chiplet_thermal/area.py
def compute_chiplet_area_breakdown(config):
    psingle = config.target_total_fp16 / config.num_chiplets
    rho = config.transistor_density
    util = config.util_factor
    eps = config.arch_efficiency
    logic_base = psingle / (rho * util * eps)

    tsv_area_um2 = (
        config.n_signal_tsv * config.area_signal_via_um2
        + config.n_power_tsv * config.area_power_via_um2
    )
    tsv_area_mm2 = tsv_area_um2 / 1e6

    n_bumps = config.n_total_bumps if config.n_total_bumps > 0 else (config.n_signal_tsv + config.n_power_tsv)
    hb_pitch_um = config.hb_bump_pitch_um
    hb_unit_area_um2 = hb_pitch_um**2
    hb_area_mm2 = n_bumps * hb_unit_area_um2 / 1e6

    chiplet_final = logic_base + tsv_area_mm2 + hb_area_mm2
    package_total = config.alpha_package * config.num_chiplets * chiplet_final
    return logic_base, chiplet_final, package_total, tsv_area_mm2, hb_area_mm2

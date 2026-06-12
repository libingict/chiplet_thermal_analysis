# chiplet_thermal/analyzer.py
import numpy as np
from .models import ChipletConfig, PowerThermalResult
from . import constants, area, power

class ThermalPowerAnalyzer:
    """Chiplet 热与功耗分析器，支持简单/分层热阻网络"""
    
    def __init__(self, config: ChipletConfig):
        self.config = config

    def analyze(self) -> PowerThermalResult:
        # 预计算 TSV 数量，根据带宽和TSV传输能力需求，确保满足带宽要求，同时考虑芯片面积和工艺限制
        rate_bps = self.config.rate_data_per_tsv_bit_s
        n_signal_tsv = self.config.bw_per_chiplet_tb_s * 8 * 1e12 / (rate_bps * 0.9) 
        n_power_tsv = n_signal_tsv * constants.POWER_TSV_RATIO
        self.config.n_signal_tsv = int(np.ceil(n_signal_tsv)) * constants.TSV_REDUNDANCY # 每个 chiplet 的信号 TSV 数量
        self.config.n_power_tsv = int(np.ceil(n_power_tsv)) * constants.TSV_REDUNDANCY  # 每个 chiplet 的电源 TSV 数量

        # 1. 面积计算
        logic_base_mm2, chiplet_final_mm2, pkg_total_mm2, tsv_area_mm2, hb_area_mm2 = area.compute_chiplet_area_breakdown(self.config)

        # 2. 功耗计算
        p_dyn_logic, p_stat_logic, p_chiplet = power.compute_chiplet_power_v2(self.config, logic_base_mm2)
        p_package = power.compute_package_power(self.config, p_chiplet)

        if self.config.use_hierarchical:
            # 单 chiplet 内部热阻 (不含 TIM)
            ct = self.config.chip_thermal
            chiplet_area_m2 = chiplet_final_mm2 * 1e-6
            r_chip = ct.compute_theta_jc_for_area(chiplet_area_m2) if ct.use_physical else ct.theta_jc # 注意这里的热阻是单个 chiplet 内部的结到表面热阻，不含 TIM 和封装热阻

            # 壳‑环境热阻 (TIM + 散热器 + 中介层)
            total_chip_area_m2 = chiplet_final_mm2 * self.config.num_chiplets * 1e-6
            pkg = self.config.package_thermal
            r_ca_base = pkg.compute_theta_ca(total_chip_area_m2) if pkg.use_physical else pkg.theta_ca

            # 系统热阻：R_system = (r_chip + r_ca_base) / N * η
            r_single = r_chip + r_ca_base
            eta = pkg.thermal_coupling_factor # 热耦合因子，考虑芯片间热耦合和非理想散热路径，通常 0.1~1.3
            r_system = (r_single / self.config.num_chiplets) * eta 

            # 均匀结温
            t_j = self.config.ambient_temp + p_package * r_system
            t_j_list = t_j
        else:
            t_j = self.config.ambient_temp + p_package * self.config.theta_ja
            t_j_list = t_j

    
        # 4. 热阻详情（分层时）
        details = None
        if self.config.use_hierarchical and self.config.chip_thermal.use_physical:
            details = self.config.chip_thermal.compute_thermal_details(chiplet_final_mm2 * 1e-6)

        return PowerThermalResult(
            num_chiplets=self.config.num_chiplets,
            logic_power_per_chiplet=p_dyn_logic + p_stat_logic,  # 逻辑总功耗（不含内存等）
            total_power_per_chiplet=p_chiplet,
            total_package_power=p_package,
            junction_temp=t_j_list,
            chiplet_area_mm2=chiplet_final_mm2,
            total_chip_area_mm2=pkg_total_mm2,
            logic_area_mm2=logic_base_mm2,
            memory_area_mm2=0.0,     # 内存面积不单独拆分，归入总面积
            interconnect_area_mm2=0.0,
            tsv_area_mm2=tsv_area_mm2,
            thermal_details=details,
        )

    
    @staticmethod
    def print_result(result: PowerThermalResult):
        print(f"\n{'='*60}")
        print(f"  Chiplet 数量:                {result.num_chiplets}")
        print(f"  单 Chiplet 面积分解:")
        print(f"    - 逻辑:                     {result.logic_area_mm2:.2f} mm²")
        print(f"    - 内存:                     {result.memory_area_mm2:.2f} mm²")
        print(f"    - 互连开销:                 {result.interconnect_area_mm2:.2f} mm²")
        print(f"    - 合计:                     {result.chiplet_area_mm2:.2f} mm²")
        print(f"  所有 Chiplet 总面积:         {result.total_chip_area_mm2:.2f} mm²")
        print(f"   - TSV 占用:                 {result.tsv_area_mm2:.2f} mm²")
        print(f"  单 Chiplet 逻辑功耗:         {result.logic_power_per_chiplet:.2f} W")
        print(f"  单 Chiplet 总功耗:           {result.total_power_per_chiplet:.2f} W")
        print(f"  封装总功耗:                  {result.total_package_power:.2f} W")
        #print(f"  芯片总结温度 (Ttotal):       {result.t_total_chip:.2f} °C" if result.t_total_chip is not None else "  芯片总结温度 (Ttotal):       N/A")
        
        if isinstance(result.junction_temp, list):
            if result.case_temp is not None:
                print(f"  外壳温度 (Tcase):            {result.case_temp:.2f} °C")
            unique_temps = set(round(t,2) for t in result.junction_temp)
            if len(unique_temps) == 1:
                print(f"  各 Chiplet 结温 (Tj):        {result.junction_temp[0]:.2f} °C (均匀)")
            else:
                for i, tj in enumerate(result.junction_temp):
                    print(f"  Chiplet {i+1} 结温:          {tj:.2f} °C")
        else:
            print(f"  结温 (Tj, 简单模型):         {result.junction_temp:.2f} °C")
        print(f"{'='*50}\n")
# main.py
from chiplet_thermal.analysis import analyze_scaling, custom_analysis#, print_physical_and_overhead_config
from chiplet_thermal.constants import (
        H200_FP16_TFLOPS, H200_TDP, H200_LOGIC_POWER,
        H200_LOGIC_EFFICIENCY, DOMESTIC_5NM_EFF
    )
if __name__ == "__main__":
    print("=== 国内5nm 3D Chiplet 热-功耗分析 (面积随chiplet数量变化) ===\n")

    print(f"参考基线: H200 FP16={H200_FP16_TFLOPS} TFLOPS, TDP={H200_TDP} W")
    print(f"估算逻辑功耗: {H200_LOGIC_POWER:.1f} W, 逻辑能效: {H200_LOGIC_EFFICIENCY:.2f} TFLOPS/W")
    print(f"国内5nm能效 (85%): {DOMESTIC_5NM_EFF:.2f} TFLOPS/W\n")

    
    # 打印物理参数与开销配置
    # print_physical_and_overhead_config()
    # 分层热模型分析
    print(">>> 分层热模型 (物理热阻 + 动态面积)")
    df_hier = analyze_scaling([2, 4, 6, 8], use_hierarchical=True)
    print("\n--- 分层模型汇总 ---")
    print(df_hier.to_string(index=False))

    # 简单模型对比
    # print("\n>>> 简单热模型 (θ_JA=0.025 °C/W)")
    # df_simple = analyze_scaling([1, 2, 4, 6, 8], use_hierarchical=False)
    # print("\n--- 简单模型汇总 ---")
    # print(df_simple.to_string(index=False))

    # # 自定义分层模型示例
    # print("\n--- (6 chiplet, 查看面积对热阻的影响) ---")
    #custom_analysis(num_chiplets=6, use_hierarchical=True)
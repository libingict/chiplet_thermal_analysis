# 3D Chiplet 热与功耗分析工具

面向 **3D Memory-on-Logic** 多 Chiplet 架构的早期评估：在 H200 FP16 算力基准与国内 5nm 类工艺假设下，估算**逻辑面积**、**单 chiplet / 封装功耗**与**结温**，并支持按 chiplet 数量做点扫描。

分析链路（与代码一致）：

1. **面积** — 由总算力目标与晶体管模型得到逻辑面积；按带宽推算 TSV 数量，叠加 TSV 与混合键合（HB）焊盘面积，再经封装系数得到封装 footprint。  
2. **功耗** — 逻辑采用 H200 功率密度 + 频率与工艺修正；内存含 bit 能量、TSV 驱动、DRAM 层刷新/漏电及 Basic Die 开销；封装含传输损耗与固定中介层功耗。  
3. **热** — **简单模型**：单 lumped \(\theta_{JA}\)；**分层模型**：DRAM / HB / Basic / Logic 叠层热阻 + TIM / 散热器（及可选中介层），多 chiplet 并联与热耦合因子 \(\eta\)。

详细公式、参数表与假设见下方 [技术文档](#技术文档)。

---

## 技术文档

| 文档 | 说明 |
|------|------|
| [**area_modeling.md**](area_modeling.md) | 逻辑面积、带宽驱动 TSV/HB 面积、封装放大；与功耗、热模型的耦合关系 |
| [**thermal_modeling.md**](thermal_modeling.md) | 简单 \(\theta_{JA}\) 与分层热阻网络、`ChipletThermal` / `PackageThermal`、结温计算 |
| [**power_estimate.md**](power_estimate.md) | 功耗推算总体框架与步骤（设计说明，含带宽–TSV、面积功耗密度法等） |

建议阅读顺序：先 [power_estimate.md](power_estimate.md) 了解设计意图，再对照 [area_modeling.md](area_modeling.md) 与 [thermal_modeling.md](thermal_modeling.md) 与实现对齐。

---

## 项目结构

| 路径 | 说明 |
|------|------|
| `chiplet_thermal/` | 核心 Python 包 |
| `chiplet_thermal/constants.py` | 基准常量（H200、工艺、面积/功耗/热默认） |
| `chiplet_thermal/models.py` | `ChipletConfig`、`PowerThermalResult` 等数据类 |
| `chiplet_thermal/area.py` | 单 chiplet 面积分解（逻辑 + TSV + HB） |
| `chiplet_thermal/power.py` | 单 chiplet 与封装功耗 |
| `chiplet_thermal/thermal_resistance.py` | `ChipletThermal`、`PackageThermal` 热阻 |
| `chiplet_thermal/analyzer.py` | `ThermalPowerAnalyzer`：TSV 预估 → 面积 → 功耗 → 结温 |
| `chiplet_thermal/analysis.py` | `analyze_scaling`、`custom_analysis`（多点扫描） |
| `chiplet_thermal/scaling_defaults.py` | 扫描/GUI/JSON 参数与 `constants` 的合并 |
| `main.py` | 示例：打印 H200 基线并对多 chiplet 数跑分层模型 |
| `gui.py` | 图形界面 + 命令行（`--cli`） |
| `examples/chiplet_thermal_params.example.json` | 参数 JSON 示例 |
| `requirements.txt` | 依赖：`numpy`、`pandas` |

---

## 环境准备

```bash
pip install -r requirements.txt
```

图形界面需要 Python 自带 **tkinter**（多数官方安装包已包含）。

---

## 快速运行

### 示例脚本

```bash
python main.py
```

默认对 chiplet 数量 `[2, 4, 6, 8]` 使用**分层热模型**输出表格。

### 图形界面

```bash
python gui.py
```

左侧配置参数（悬停可看说明），右侧查看结果；支持「分层模型 / 简单模型」、**保存/载入 JSON**、**导出 CSV**。

用示例 JSON 预填表单：

```bash
python gui.py --config examples/chiplet_thermal_params.example.json
```

### 命令行批跑（无 GUI）

```bash
python gui.py --cli --chiplets 2,4,8 --hierarchical
python gui.py --cli --config examples/chiplet_thermal_params.example.json -o results.csv
python gui.py --cli --help
```

| 参数 | 作用 |
|------|------|
| `--cli` | 终端运行，打印结果表 |
| `--chiplets` | 逗号分隔的 chiplet 数量列表（默认 `4`） |
| `--hierarchical` | 启用分层物理热阻 |
| `--config PATH` | JSON 参数文件 |
| `-o` / `--output` | 结果写入 UTF-8 CSV（带 BOM，便于 Excel） |
| `--target-fp16`、`--ambient`、`--theta-ja` | 覆盖总算力、环境温度、简单模型 \(\theta_{JA}\) |

---

## 参数 JSON

与 GUI「保存 JSON」格式相同；可复制 [examples/chiplet_thermal_params.example.json](examples/chiplet_thermal_params.example.json) 后修改。

- **表单字段 id**：如 `target_total_fp16`、`f_clk_ghz`、`hb_thermal_mm2kw`（使用界面工程单位）。  
- **扫描控制**：`chiplet_counts`（数组）、`use_hierarchical`（布尔）。  
- **说明键**：如 `_comment` 会被忽略。  
- **仅 API 关键字**（SI 单位，且与表单 id 不同名）：可额外传入 `analyze_scaling` 参数；与表单 id 同名的键只按表单单位解析一次。

字段完整列表见 `gui.py` 中的 `FORM_FIELDS`。

---

## 在代码中调用

```python
from chiplet_thermal import (
    ThermalPowerAnalyzer,
    ChipletConfig,
    ProcessNode,
    analyze_scaling,
    custom_analysis,
)

# 多点扫描 → pandas.DataFrame
df = analyze_scaling([2, 4, 8], use_hierarchical=True)

# 单次分析
# cfg = ChipletConfig(num_chiplets=4, target_total_fp16=1979.0, process=ProcessNode("ref", 0.0), use_hierarchical=True)
# result = ThermalPowerAnalyzer(cfg).analyze()
```

---

## 输出说明

`analyze_scaling` / `ThermalPowerAnalyzer` 典型结果列包括：逻辑面积、单 chiplet 面积、封装总面积、逻辑功耗、单 chiplet 总功耗、封装总功耗、结温（°C）。分层模型下结温随 chiplet 数量、面积与功耗共同变化；具体敏感性见 [thermal_modeling.md](thermal_modeling.md) 与 [area_modeling.md](area_modeling.md)。

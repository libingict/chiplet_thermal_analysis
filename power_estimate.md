# Chiplet功耗推算技术文档

## 1. 文档概述

### 1.1 目标

设计一款对标现有大算力GPU的Chiplet架构GPU，计算单个Chiplet及系统总功耗。

### 1.2 架构特征

- **Chiplet数量**: N个
- **单Chiplet架构**: 3D Memory-on-Logic (GPU Logic + Basic Logic Die + 3D DRAM)
- **堆叠技术**: TSV + 混合键合
- **工艺**: 国内5nm （假设）
- **存储技术**: CXMT 3D
- **散热**: 风冷（目标约束）

---

## 2. 功耗推算总体框架

```
总功耗 = N × 单Chiplet功耗
单Chiplet功耗 = 逻辑功耗 + 存储功耗 + 系统开销
```

---

## 3. 详细推算步骤

### 步骤1: 确定单Chiplet算力目标

**公式3.1: 单Chiplet算力**
$$Perf_{single} = \frac{Perf_{total}}{N}$$

**参数说明:**

- $Perf_{total}$: 系统总目标算力 (1979 TFLOPS)
- $N$: Chiplet数量
- $Perf_{single}$: 单Chiplet目标算力

**示例计算:**
$$Perf_{single} = \frac{1979}{4} = 494.75 \text{ TFLOPS}$$

---

### 步骤2: 计算带宽-算力比（β）

**公式3.2: 带宽-算力比**
$$\beta = \frac{BW_{H200}}{Perf_{H200}}$$

**参数说明:**

- $BW_{H200}$: H200总内存带宽 (4.8 TB/s)
- $Perf_{H200}$: H200总算力 (1979 TFLOPS)
- $\beta$: 每次运算所需的平均数据传输量 (Bytes/Op)

**计算:**
$$\beta = \frac{4.8 \times 10^{12}\ \text{Bytes/s}}{1979 \times 10^{12}\ \text{FLOP/s}} \approx 2.427\times 10^{-3}\ \text{Bytes/Op}$$

---

### 步骤3: 计算单Chiplet目标带宽

**公式3.3: 单Chiplet带宽**
$$BW_{single} = Perf_{single} \times \beta$$

**计算:**
$$BW_{single} = 494.75\times 10^{12}\ \text{FLOP/s} \times 2.427\times10^{-3}\ \text{Bytes/Op} \approx 1.20\times10^{12}\ \text{Bytes/s} = 1.2\ \text{TB/s}$$

---

### 步骤4: 计算TSV信号数量

**公式3.4: TSV信号数量**
$$N_{tsv} = \frac{BW_{single} \times 8}{R_{pin} \times \eta_{code}}$$

**参数说明:**

- $BW_{single}$: 单Chiplet带宽 (Byte/s)
- $8$: Byte转bit的系数
- $R_{pin}$: 单个TSV/信号线数据速率 (bit/s)
- $\eta_{code}$: 编码效率 (考虑8b/10b、128b/130b等编码开销)

**典型参数:**

- $R_{pin} = 6.4 \text{ Gbps} = 6.4 \times 10^9 \text{ bit/s}$
- $\eta_{code} = 0.9$ (10%编码开销)

**计算:**
$$N_{tsv} = \frac{1.2 \times 10^{12} \times 8}{6.4 \times 10^9 \times 0.9} = \frac{9.6 \times 10^{12}}{5.76 \times 10^9} = 1667 \text{ 个}$$

**工程修正:**
实际设计需考虑冗余、电源/地TSV，通常乘以1.5-2倍安全系数：
$$N_{tsvactual} = N_{tsv} \times \rho_{safety} = 1667 \times 2 = 3334 \text{ 个}$$

---

### 步骤5: 逻辑部分功耗计算（工程化方法）

#### 5.1 面积功耗密度法（主推算法）

**公式3.5: 基础逻辑功耗**
$$P_{logicbase} = A_{logic} \times \rho_{power}$$

**参数说明:**

- $A_{logic}$: 逻辑面积 (mm²)
- $\rho_{power}$: 功耗密度 (W/mm²)，参考H100实测值0.86 W/mm²

**公式3.6: 频率缩放**
$$P_{logicfreq} = P_{logicbase} \times \frac{f_{target}}{f_{ref}}$$

**参数说明:**

- $f_{target}$: 目标工作频率
- $f_{ref}$: 参考频率 (H100约1.8 GHz)

**公式3.7: 工艺修正**
$$P_{logictotal} = P_{logicfreq} \times \alpha_{process}$$

**参数说明:**

- $\alpha_{process}$: 工艺惩罚系数 (国产5nm相对于台积电4N/5nm)

**完整公式:**
$$P_{logictotal} = A_{logic} \times \rho_{power} \times \frac{f_{target}}{f_{ref}} \times \alpha_{process}$$

**示例计算:**
$$P_{logictotal} = 567 \times 0.86 \times \frac{1.6}{1.8} \times 1.2 = 519.7 \text{ W}$$

#### 5.2 动态/静态功耗分解

**公式3.8: 动态功耗**
$$P_{logicdyn} = P_{logictotal} \times r_{dyn}$$

**公式3.9: 静态功耗**
$$P_{logicstat} = P_{logictotal} \times r_{stat}$$

**典型参数:**

- $r_{dyn} = 0.8$ (动态功耗占比80%)
- $r_{stat} = 0.2$ (静态功耗占比20%)

**计算:**
$$P_{logicdyn} = 519.7 \times 0.8 = 415.8 \text{ W}$$
$$P_{logicstat} = 519.7 \times 0.2 = 103.9 \text{ W}$$

---

### 步骤6: 存储部分功耗计算

#### 6.1 阵列动态功耗

**公式3.10: 阵列动态功耗**
$$P_{memarray} = BW_{single} \times 8 \times E_{bit}$$

**参数说明:**

- $E_{bit}$: 单位比特访问能耗 (J/bit)，HBM3典型值2.5 pJ/bit = $2.5 \times 10^{-12}$ J/bit

**计算:**
$$P_{memarray} = 1.2 \times 10^{12} \times 8 \times 2.5 \times 10^{-12} = 24.0 \text{ W}$$

#### 6.2 TSV接口驱动功耗

**公式3.11: TSV驱动功耗**
$$P_{memtsv} = N_{tsv} \times P_{driver}$$

**参数说明:**

- $P_{driver}$: 单个高速驱动器功耗 (W/pin)，典型值1.5 mW = 0.0015 W

**计算:**
$$P_{memtsv} = 3334 \times 0.0015 = 5.0 \text{ W}$$

#### 6.3 存储静态功耗

**公式3.12: 存储静态功耗**
$$P_{memstat} = N_{layers} \times (P_{refresh} + P_{leak})$$

**参数说明:**

- $N_{layers}$: DRAM堆叠层数 (典型8层)
- $P_{refresh}$: 单层刷新功耗 (典型0.5 W)
- $P_{leak}$: 单层漏电功耗 (典型0.1 W)

**计算:**
$$P_{memstat} = 8 \times (0.5 + 0.1) = 4.8 \text{ W}$$

#### 6.4 存储总功耗

**公式3.13: 存储总功耗**
$$P_{memtotal} = P_{memarray} + P_{memtsv} + P_{memstat}$$

**计算:**
$$P_{memtotal} = 24.0 + 5.0 + 4.8 = 33.8 \text{ W}$$

---

### 步骤7: 系统开销计算

**公式3.14: 系统开销**
$$P_{overhead} = (P_{logictotal} + P_{memtotal}) \times r_{overhead}$$

**参数说明:**

- $r_{overhead}$: 系统开销比例 (典型3%)

**计算:**
$$P_{overhead} = (519.7 + 33.8) \times 0.03 = 16.6 \text{ W}$$

---

### 步骤8: 单Chiplet总功耗

**公式3.15: 单Chiplet总功耗**
$$P_{chiplet} = P_{logictotal} + P_{memtotal} + P_{overhead}$$

**计算:**
$$P_{chiplet} = 519.7 + 33.8 + 16.6 = 570.1 \text{ W}$$

---

### 步骤9: 系统总功耗

**公式3.16: 系统总功耗**
$$P_{system} = N \times P_{chiplet}$$

**计算:**
$$P_{system} = 4 \times 570.1 = 2280.4 \text{ W}$$

---

## 4. 完整推算公式汇总

### 4.1 核心公式链

$$
\begin{aligned}
&\text{1. 单Chiplet算力:} & Perf_{single} &= \frac{Perf_{total}}{N} 
&\text{2. 带宽-算力比:} & \beta &= \frac{BW_{H200}}{Perf_{H200}} 
&\text{3. 单Chiplet带宽:} & BW_{single} &= Perf_{single} \times \beta 
&\text{4. TSV数量:} & N_{tsv} &= \frac{BW_{single} \times 8}{R_{pin} \times \eta_{code}} \times \rho_{safety} 
&\text{5. 逻辑总功耗:} & P_{logictotal} &= A_{logic} \times \rho_{power} \times \frac{f_{target}}{f_{ref}} \times \alpha_{process} 
&\text{6. 逻辑动态功耗:} & P_{logicdyn} &= P_{logictotal} \times r_{dyn} 
&\text{7. 逻辑静态功耗:} & P_{logicstat} &= P_{logictotal} \times r_{stat} 
&\text{8. 阵列动态功耗:} & P_{memarray} &= BW_{single} \times 8 \times E_{bit} 
&\text{9. TSV驱动功耗:} & P_{memtsv} &= N_{tsv} \times P_{driver} 
&\text{10. 存储静态功耗:} & P_{memstat} &= N_{layers} \times (P_{refresh} + P_{leak}) 
&\text{11. 存储总功耗:} & P_{memtotal} &= P_{memarray} + P_{memtsv} + P_{memstat} 
&\text{12. 系统开销:} & P_{overhead} &= (P_{logictotal} + P_{memtotal}) \times r_{overhead} 
&\text{13. 单Chiplet功耗:} & P_{chiplet} &= P_{logictotal} + P_{memtotal} + P_{overhead} 
&\text{14. 系统总功耗:} & P_{system} &= N \times P_{chiplet}
\end{aligned}
$$

---

## 5. 参数表

### 5.1 目标参数


| 参数        | 符号             | 值    | 单位     | 说明     |
| --------- | -------------- | ---- | ------ | ------ |
| 总算力       | $Perf_{total}$ | 1979 | TFLOPS | 对标H200 |
| Chiplet数量 | $N$            | 4    | -      | 可变参数   |
| H200带宽    | $BW_{H200}$    | 4.8  | TB/s   | 参考值    |


### 5.2 架构参数


| 参数     | 符号              | 值   | 单位   | 说明     |
| ------ | --------------- | --- | ---- | ------ |
| 逻辑面积   | $A_{logic}$     | 567 | mm²  | 投影面积   |
| 工作频率   | $f_{target}$    | 1.6 | GHz  | 目标频率   |
| DRAM层数 | $N_{layers}$    | 8   | 层    | HBM3标准 |
| TSV速率  | $R_{pin}$       | 6.4 | Gbps | 单引脚速率  |
| 编码效率   | $\eta_{code}$   | 0.9 | -    | 含10%开销 |
| 安全系数   | $\rho_{safety}$ | 2.0 | -    | 冗余设计   |


### 5.3 工艺参数


| 参数   | 符号                 | 值    | 单位    | 说明     |
| ---- | ------------------ | ---- | ----- | ------ |
| 功耗密度 | $\rho_{power}$     | 0.86 | W/mm² | H100实测 |
| 参考频率 | $f_{ref}$          | 1.8  | GHz   | H100频率 |
| 工艺惩罚 | $\alpha_{process}$ | 1.2  | -     | 国产5nm  |
| 动态占比 | $r_{dyn}$          | 0.8  | -     | 典型值    |
| 静态占比 | $r_{stat}$         | 0.2  | -     | 典型值    |


### 5.4 存储参数


| 参数     | 符号             | 值    | 单位     | 说明     |
| ------ | -------------- | ---- | ------ | ------ |
| 单位比特能耗 | $E_{bit}$      | 2.5  | pJ/bit | HBM3典型 |
| 驱动器功耗  | $P_{driver}$   | 1.5  | mW/pin | 高速驱动   |
| 刷新功耗   | $P_{refresh}$  | 0.5  | W/层    | 单层刷新   |
| 漏电功耗   | $P_{leak}$     | 0.1  | W/层    | 单层漏电   |
| 系统开销   | $r_{overhead}$ | 0.03 | -      | 3%     |


---

## 6. 工程验证方法

### 6.1 理论公式验证

**动态功耗理论公式:**
$$P_{dyntheory} = \alpha \times C_{total} \times V_{dd}^2 \times f$$

**静态功耗理论公式:**
$$P_{stattheory} = A \times J_{leak} \times V_{dd}$$

**验证指标:**
$$Ratio = \frac{P_{theory}}{P_{engineering}}$$

- $Ratio < 1$: 理论公式低估，需工程修正
- $Ratio \approx 1$: 理论与工程一致
- $Ratio > 1$: 理论公式高估

---

## 7. 附录：参考数据

### 7.1 H100/H200实测数据

- H100: 814mm², 700W → 0.86 W/mm²
- A100: 826mm², 400W → 0.48 W/mm²
- H200: 4.8 TB/s带宽, 1979 TFLOPS

### 7.2 HBM3技术参数

- 单引脚速率: 6.4 Gbps
- 堆叠层数: 8-12层
- 单位比特能耗: 2.0-3.0 pJ/bit

---

**文档版本**: V2.0  
**最后更新**: 2026-05-11  
**作者**: Bing Li

---

# English version (complete translation)

This is the English translation of the full Chinese power estimation document. It preserves structure, formulas, and example calculations.

# Chiplet Power Estimation (English)

## 1. Overview

Goal: estimate per-chiplet and system total power for a chiplet-based GPU architecture targeting large compute (e.g., comparable to H200).

Key features: N chiplets, 3D Memory-on-Logic stacking, TSV + hybrid-bond, assumed process (domestic 5nm), HBM-like memory, and air cooling.

---

## 2. Overall power estimation flow

Total power = N × single-chiplet power
Single-chiplet power = logic power + memory power + system overhead

---

## 3. Detailed estimation steps

### Step 1: Single-chiplet performance target

$Perf_{single} = Perf_{total} / N$

Example: Perf_{single} = 1979 / 4 = 494.75 TFLOPS

### Step 2: Bandwidth-to-FLOP ratio (β)

\[
\beta = \frac{BW_{H200}}{Perf_{H200}}
\]

Where $BW_{H200}$ = 4.8 TB/s (bytes per second), $Perf_{H200}$ = 1979 TFLOPS (FLOP/s). Using consistent SI units:

\[
\beta = \frac{4.8\times10^{12}\ \mathrm{Bytes/s}}{1979\times10^{12}\ \mathrm{FLOP/s}} \approx 2.427\times10^{-3}\ \mathrm{Bytes/Op}
\]

### Step 3: Single-chiplet bandwidth

\[
BW_{single} = Perf_{single} \times \beta
\]

Using $Perf_{single}$ = 494.75×10^{12} FLOP/s:

\[
BW_{single} = 494.75\times10^{12} \times 2.427\times10^{-3} \approx 1.20\times10^{12}\ \mathrm{Bytes/s} = 1.2\ \mathrm{TB/s}
\]

### Step 4: TSV signal count

\[
N_{tsv} = \frac{BW_{single}\times 8}{R_{pin}\times \eta_{code}}
\]

Using $R_{pin}=6.4e9 bit/s$ and $η_{code}=0.9$ gives $N_{tsv} ≈ 1667$. Apply safety factor (e.g. ×2) to account for redundancy and P/G TSVs.

### Step 5: Logic power (engineering method)

Base logic power via area-power density method:

\[
P_{logicbase} = A_{logic} \times \rho_{power}
\]

Frequency and process scalings:

\[
P_{logictotal} = A_{logic} \times \rho_{power} \times \frac{f_{target}}{f_{ref}} \times \alpha_{process}
\]

Example: 567 mm², 0.86 W/mm², $f_{target}=1.6 GHz$, $f_{ref}=1.8 GHz$, $α_{process}=1.2$ gives $P_{logictotal} ≈ 519.7 W$.

Split into dynamic/static fractions: $r_{dyn}=0.8$, $r_{stat}=0.2$.

### Step 6: Memory power

Array dynamic:

\[
P_{memarray} = BW_{single} \times 8 \times E_{bit}
\]

With $E_{bit}=2.5 pJ/bit → P_{memarray} ≈ 24.0 W (for 1.2 TB/s)$.

TSV driver power:

\[
P_{memtsv} = N_{tsv} \times P_{driver}
\]

With $P_{driver}=1.5 mW → ~5.0 W$ (after applying $N_{tsvactual}$).

Memory static (refresh + leak): $P_{memstat} = N_{layers} × (P_{refresh} + P_{leak})$. Example 8×(0.5+0.1)=4.8 W.

Total memory ≈ 33.8 W.

### Step 7: System overhead

\[
P_{overhead} = (P_{logictotal} + P_{memtotal}) \times r_{overhead}
\]

With $r_{overhead}=0.03 gives ~16.6 W$.

### Step 8: Single-chiplet total

\[
P_{chiplet} = P_{logictotal} + P_{memtotal} + P_{overhead} \approx 570.1\ \mathrm{W}
\]

### Step 9: System total

\[
P_{system} = N \times P_{chiplet} \approx 4 \times 570.1 = 2280.4\ \mathrm{W}
\]

---

## 4. Core formula summary (English)

(Translate of the Chinese formula block, preserving math and variable names.)


---



 
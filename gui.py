#!/usr/bin/env python3
# gui.py — Chiplet 热/功耗/面积分析：图形界面 + 命令行
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Dict, List, Optional

import tkinter as tk
from tkinter import ttk, scrolledtext

import inspect

from chiplet_thermal.analysis import analyze_scaling
from chiplet_thermal import constants as const

_ANALYZE_KEYS = frozenset(inspect.signature(analyze_scaling).parameters.keys())


# ---------------------------------------------------------------------------
# Field model: stable `id` for JSON/CLI, human `label` + `hint` for GUI
# ---------------------------------------------------------------------------
def _f(
    fid: str,
    label: str,
    ptype: str,
    default: Any,
    unit: str = "",
    hint: str = "",
    *,
    widget: str = "entry",
) -> Dict[str, Any]:
    return {
        "id": fid,
        "label": label,
        "ptype": ptype,
        "default": default,
        "unit": unit,
        "hint": hint,
        "widget": widget,
    }


def _section(title: str) -> Dict[str, Any]:
    return {"kind": "section", "title": title}


FORM_FIELDS: List[Dict[str, Any]] = [
    _section("系统"),
    _f(
        "target_total_fp16",
        "总算力目标 (TFLOPS)",
        "float",
        const.H200_FP16_TFLOPS,
        "",
        "参考：H200 FP16 稠密峰值约 1979；可按产品目标修改。",
    ),
    _f(
        "num_chiplets",
        "Chiplet 数量",
        "int",
        4,
        "",
        "本次运行只分析该数量；命令行可用 --chiplets 2,4,8 做多点扫描。",
    ),
    _section("面积模型"),
    _f(
        "transistor_density",
        "晶体管密度 (M/mm²)",
        "float",
        const.TRANSISTOR_DENSITY,
        "M/mm²",
        "约 150 表示 1.5×10⁸ /mm²；密度越高同样算力面积越小。",
    ),
    _f(
        "util_factor",
        "利用率系数",
        "float",
        const.UTIL_FACTOR,
        "",
        "有效晶体管占布局的比例，常见约 0.35~0.5。",
    ),
    _f(
        "arch_efficiency",
        "架构效率 (TFLOPS/M)",
        "float",
        const.ARCH_EFFICIENCY,
        "TFLOPS/M",
        "单位晶体管质量算力；与利用率共同决定逻辑面积。",
    ),
    _f(
        "area_signal_via_um2",
        "单信号 TSV 占用 (μm²)",
        "float",
        const.AREA_SIGNAL_VIA_UM2,
        "μm²",
        "含 KOZ 等隔离区的等效面积，偏大则总面积上升。",
    ),
    _f(
        "area_power_via_um2",
        "单电源 TSV 占用 (μm²)",
        "float",
        const.AREA_POWER_VIA_UM2,
        "μm²",
        "电源 TSV 通常比信号 TSV 更粗。",
    ),
    _f(
        "hb_bump_pitch_um",
        "HB 焊盘 pitch (μm)",
        "float",
        const.HB_BUMP_PITCH_UM,
        "μm",
        "混合键合焊盘间距；pitch 越小焊盘密度越高、键合面积越大。",
    ),
    _f(
        "alpha_package",
        "封装放大系数 α",
        "float",
        const.ALPHA_PACKAGE,
        "",
        "封装级面积相对裸芯总和的放大，典型约 1.25~1.4。",
    ),
    _section("功耗 — 逻辑"),
    _f(
        "alpha_activity",
        "开关活动因子 α",
        "float",
        const.ALPHA_ACTIVITY,
        "",
        "电容模型路径用；v2 功率模型主要参考 H200 功率密度。",
    ),
    _f(
        "c_unit_f_per_mm2_ff",
        "单位面积电容 (fF/mm²)",
        "float",
        const.C_UNIT_F_PER_MM2 * 1e15,
        "fF/mm²",
        "例如 150 fF/mm² 对应 1.5e-13 F/mm²（电容模型用）。",
    ),
    _f("vdd", "工作电压 Vdd (V)", "float", const.VDD, "V", "先进节点常见 0.75~0.9 V。"),
    _f(
        "f_clk_ghz",
        "时钟频率 (GHz)",
        "float",
        const.F_CLK * 1e-9,
        "GHz",
        "逻辑动态功耗随频率近似线性缩放（相对 H200 基准频率）。",
    ),
    _f(
        "j_leakage_a_per_mm2",
        "漏电流密度 (A/mm²)",
        "float",
        const.J_LEAKAGE_A_PER_MM2,
        "A/mm²",
        "高温、高漏电角点可适当上调。",
    ),
    _section("功耗 — 内存 / IO"),
    _f(
        "e_bit_pj",
        "单位比特能耗 (pJ/bit)",
        "float",
        const.E_BIT_PJ * 1e12,
        "pJ/bit",
        "HBM 类接口量级常取 2~3 pJ/bit 量级做估算。",
    ),
    _f(
        "bw_per_chiplet_tb_s",
        "每 chiplet 带宽 (TB/s)",
        "float",
        const.BW_PER_CHIPLET_TB_S,
        "TB/s",
        "与 TSV 速率共同决定所需信号 TSV 数量。",
    ),
    _f(
        "p_tsv_driver_mw",
        "单 TSV 驱动功耗 (mW)",
        "float",
        const.P_TSV_DRIVER_PER_SIGNAL_W * 1000,
        "mW",
        "保守估计可取 1~2 mW/通道。",
    ),
    _f(
        "rate_data_gbps",
        "单 TSV 串行速率 (Gbps)",
        "float",
        const.RATE_DATA_PER_TSV_BIT_S * 1e-9,
        "Gbps",
        "与带宽一起决定 TSV 条数；内部换算为 bit/s。",
    ),
    _f(
        "p_refresh_per_die",
        "单层 DRAM 刷新功耗 (W)",
        "float",
        const.P_REFRESH_PER_DIE_W,
        "W",
        "每层刷新功耗经验值，可按厂商数据调整。",
    ),
    _f(
        "p_leak_per_die",
        "单层 DRAM 漏电功耗 (W)",
        "float",
        const.P_LEAK_PER_DIE_W,
        "W",
        "DRAM 堆叠层数在「热阻」区填写，与该项相乘得静态内存功耗。",
    ),
    _f(
        "basic_overhead_ratio",
        "Basic Die 开销比例",
        "float",
        const.BASIC_OVERHEAD_RATIO,
        "",
        "基底/互连等相对核心功耗的附加比例，常见约 3%。",
    ),
    _section("封装级功耗"),
    _f(
        "package_loss_ratio",
        "电源传输损耗系数",
        "float",
        const.PACKAGE_LOSS_RATIO,
        "",
        "封装 IR 与 VRM 损耗等，用 (1+系数) 放大总芯片功耗。",
    ),
    _f(
        "interposer_power_total",
        "中介层总功耗 (W)",
        "float",
        const.INTERPOSER_POWER_TOTAL_W,
        "W",
        "SerDes、互连等不随 chiplet 数简单缩放的部分，可估为常数项。",
    ),
    _section("热环境"),
    _f(
        "ambient_temp",
        "环境温度 (°C)",
        "float",
        const.AMBIENT_TEMP,
        "°C",
        "机柜进风或冷板入口温度类边界。",
    ),
    _f(
        "theta_ja",
        "简单模型 θ_JA (°C/W)",
        "float",
        const.THETA_JA_SIMPLE,
        "°C/W",
        "仅「简单热模型」使用；分层模型走物理热阻网络。",
    ),
    _section("热阻 — Chiplet 堆叠"),
    _f(
        "num_dram_layers",
        "DRAM 层数",
        "int",
        const.N_DRAM_LAYERS,
        "",
        "同时用于 DRAM 静态功耗与 DRAM 叠层热阻厚度。",
    ),
    _f(
        "dram_thickness_um",
        "单层 DRAM 厚度 (μm)",
        "float",
        const.DRAM_THICKNESS * 1e6,
        "μm",
        "典型 3D DRAM 单层约 30~60 μm。",
    ),
    _f(
        "basic_thickness_um",
        "Basic Die 厚度 (μm)",
        "float",
        const.BASIC_THICKNESS * 1e6,
        "μm",
        "硅中介 / 基底有源层等效厚度量级。",
    ),
    _f(
        "logic_thickness_um",
        "Logic 层厚度 (μm)",
        "float",
        const.LOGIC_THICKNESS * 1e6,
        "μm",
        "GPU 逻辑 die 等效导热厚度。",
    ),
    _f(
        "k_si",
        "硅导热系数 (W/m·K)",
        "float",
        const.SI_K,
        "W/m·K",
        "纯硅约 120~150；掺杂与界面会降低等效值。",
    ),
    _f(
        "hb_thermal_mm2kw",
        "HB 界面热阻密度 (mm²·K/W)",
        "float",
        const.HB_THERMAL_RES_DENSITY * 1e6,
        "mm²·K/W",
        "与 ChipletThermal.hb_thermal_density 一致；SI 为 m²·K/W（此处 ×10⁶）。",
    ),
    _f(
        "tim_thickness_um",
        "TIM 厚度 (μm)",
        "float",
        const.TIM_THICKNESS * 1e6,
        "μm",
        "Die 到散热器 / 冷板之间的界面材料厚度。",
    ),
    _f(
        "tim_k",
        "TIM 导热系数 (W/m·K)",
        "float",
        const.TIM_K,
        "W/m·K",
        "典型聚合物 TIM 约 3~8；液态金属更高。",
    ),
    _section("封装散热（物理模型）"),
    _f(
        "use_physical_package",
        "启用物理散热模型",
        "bool",
        True,
        "",
        "勾选：鳍片 + 对流 + TIM；不勾选：使用 PackageThermal 默认 θ_ca。",
        widget="check",
    ),
    _f(
        "fin_area_ratio",
        "鳍片面积倍数",
        "float",
        const.FIN_AREA_RATIO,
        "",
        "相对裸芯面积的散热器有效扩展倍数。",
    ),
    _f(
        "fin_efficiency",
        "鳍片效率",
        "float",
        const.FIN_EFFICIENCY,
        "",
        "0~1，考虑气流不均与旁路。",
    ),
    _f(
        "thermal_coupling_factor",
        "热耦合因子 η",
        "float",
        const.THERMAL_COUPLING_FACTOR,
        "",
        "多 chiplet 热耦合与路径非理想，常取 1.0~1.3。",
    ),
    _f(
        "use_interposer_thermal",
        "计入中介层热阻",
        "bool",
        const.USE_INTERPOSER_THERMAL,
        "",
        "在结到环境路径上串联 interposer 导热项。",
        widget="check",
    ),
    _f(
        "interposer_thickness_mm",
        "中介层厚度 (mm)",
        "float",
        const.INTERPOSER_THICKNESS * 1e3,
        "mm",
        "玻璃 / 有机中介层厚度。",
    ),
    _f(
        "interposer_k",
        "中介层导热系数 (W/m·K)",
        "float",
        const.INTERPOSER_K,
        "W/m·K",
        "玻璃偏低、硅中介更高。",
    ),
]

_FORM_FIELD_IDS = frozenset(row["id"] for row in FORM_FIELDS if row.get("id"))


def default_form_values() -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for row in FORM_FIELDS:
        if row.get("kind") == "section":
            continue
        out[row["id"]] = row["default"]
    return out


def _parse_scalar(val: str, ptype: str) -> Any:
    val = val.strip()
    if ptype == "int":
        return int(float(val))
    if ptype == "float":
        return float(val)
    if ptype == "bool":
        return val.lower() in ("1", "true", "yes", "on")
    return val


def form_values_to_analyze_kwargs(
    f: Dict[str, Any],
    *,
    chiplet_counts: Optional[List[int]] = None,
    use_hierarchical: bool = False,
) -> Dict[str, Any]:
    counts = chiplet_counts if chiplet_counts is not None else [int(f["num_chiplets"])]
    return dict(
        chiplet_counts=counts,
        use_hierarchical=use_hierarchical,
        target_total_fp16=float(f["target_total_fp16"]),
        transistor_density=float(f["transistor_density"]),
        util_factor=float(f["util_factor"]),
        arch_efficiency=float(f["arch_efficiency"]),
        area_signal_via_um2=float(f["area_signal_via_um2"]),
        area_power_via_um2=float(f["area_power_via_um2"]),
        hb_bump_pitch_um=float(f["hb_bump_pitch_um"]),
        alpha_package=float(f["alpha_package"]),
        alpha_activity=float(f["alpha_activity"]),
        c_unit_f_per_mm2=float(f["c_unit_f_per_mm2_ff"]) * 1e-15,
        vdd=float(f["vdd"]),
        f_clk=float(f["f_clk_ghz"]) * 1e9,
        j_leakage_a_per_mm2=float(f["j_leakage_a_per_mm2"]),
        e_bit_pj=float(f["e_bit_pj"]) * 1e-12,
        bw_per_chiplet_tb_s=float(f["bw_per_chiplet_tb_s"]),
        p_tsv_driver_per_signal=float(f["p_tsv_driver_mw"]) * 1e-3,
        rate_data_per_tsv_bit_s=float(f["rate_data_gbps"]) * 1e9,
        num_dram_layers=int(f["num_dram_layers"]),
        p_refresh_per_die=float(f["p_refresh_per_die"]),
        p_leak_per_die=float(f["p_leak_per_die"]),
        basic_overhead_ratio=float(f["basic_overhead_ratio"]),
        package_loss_ratio=float(f["package_loss_ratio"]),
        interposer_power_total=float(f["interposer_power_total"]),
        ambient_temp=float(f["ambient_temp"]),
        theta_ja=float(f["theta_ja"]),
        dram_thickness=float(f["dram_thickness_um"]) * 1e-6,
        basic_thickness=float(f["basic_thickness_um"]) * 1e-6,
        logic_thickness=float(f["logic_thickness_um"]) * 1e-6,
        k_si=float(f["k_si"]),
        hb_thermal_res_density=float(f["hb_thermal_mm2kw"]) * 1e-6,
        tim_thickness=float(f["tim_thickness_um"]) * 1e-6,
        tim_k=float(f["tim_k"]),
        use_physical_package=bool(f["use_physical_package"]),
        fin_area_ratio=float(f["fin_area_ratio"]),
        fin_efficiency=float(f["fin_efficiency"]),
        thermal_coupling_factor=float(f["thermal_coupling_factor"]),
        use_interposer_thermal=bool(f["use_interposer_thermal"]),
        interposer_thickness=float(f["interposer_thickness_mm"]) * 1e-3,
        interposer_k=float(f["interposer_k"]),
    )


def merge_config_into_form(base: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge JSON overrides into form defaults (form field ids and a few aliases)."""
    out = dict(base)
    alias = {"chiplets": "num_chiplets", "chiplet_count": "num_chiplets"}
    for k, v in config.items():
        if v is None:
            continue
        if k == "chiplet_counts" and isinstance(v, list) and v and "num_chiplets" in out:
            out["num_chiplets"] = int(v[0])
            continue
        if k == "use_hierarchical":
            continue
        key = alias.get(k, k)
        if key not in out:
            continue
        spec = next((r for r in FORM_FIELDS if r.get("id") == key), None)
        if not spec:
            continue
        if spec["ptype"] == "bool":
            out[key] = bool(v)
        elif spec["ptype"] == "int":
            out[key] = int(v)
        elif spec["ptype"] == "float":
            out[key] = float(v)
        else:
            out[key] = v
    return out


def load_form_json(path: Path) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as fp:
        data = json.load(fp)
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return data


# ---------------------------------------------------------------------------
# Tooltips & theme
# ---------------------------------------------------------------------------
class ToolTip:
    def __init__(self, widget: tk.Widget, text: str):
        self.widget = widget
        self.text = text or ""
        self._win: Optional[tk.Toplevel] = None
        self._after_id: Optional[Any] = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)

    def _cancel_scheduled(self) -> None:
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def _schedule(self, _event=None):
        self._cancel_scheduled()
        self._after_id = self.widget.after(450, self._show)

    def _show(self):
        self._after_id = None
        if self._win or not self.text.strip():
            return
        x = self.widget.winfo_rootx() + 24
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self._win = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",
            foreground="#222",
            relief=tk.SOLID,
            borderwidth=1,
            font=("SF Pro Text", 10) if sys.platform == "darwin" else ("Segoe UI", 10),
            padx=8,
            pady=6,
            wraplength=360,
        )
        lbl.pack()

    def _hide(self, _event=None):
        self._cancel_scheduled()
        if self._win:
            try:
                self._win.destroy()
            except tk.TclError:
                pass
            self._win = None


def apply_theme(root: tk.Tk) -> None:
    root.option_add("*Font", "TkDefaultFont 11")
    try:
        style = ttk.Style(root)
        if sys.platform == "darwin":
            style.theme_use("aqua")
        else:
            style.theme_use("clam")
        style.configure("Header.TLabel", font=("TkDefaultFont", 16, "bold"))
        style.configure("Subheader.TLabel", font=("TkDefaultFont", 11), foreground="#555")
        style.configure("Hint.TLabel", font=("TkDefaultFont", 9), foreground="#666")
        style.configure("Section.TLabel", font=("TkDefaultFont", 11, "bold"), foreground="#1a1a2e")
        style.configure("Card.TFrame", background="#fafafa")
        style.configure("TLabel", background="#fafafa")
        style.configure("TFrame", background="#fafafa")
        style.configure("TLabelframe", background="#fafafa")
        style.configure("TLabelframe.Label", background="#fafafa", font=("TkDefaultFont", 12, "bold"))
    except tk.TclError:
        pass
    root.configure(bg="#ececf0")


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------
class ThermalGUI:
    def __init__(self, root: tk.Tk, *, initial_values: Optional[Dict[str, Any]] = None):
        self.root = root
        root.title("Chiplet 热 / 功耗 / 面积分析")
        root.minsize(1080, 720)
        root.geometry("1280x900")

        self._defaults = default_form_values()
        self._values: Dict[str, Any] = dict(self._defaults)
        if initial_values:
            self._values = merge_config_into_form(self._values, initial_values)

        self._vars: Dict[str, Any] = {}
        self._entries: Dict[str, tk.Widget] = {}
        self._wheel_bound = False
        self._last_df: Optional[Any] = None

        self.create_widgets()

    def _bind_canvas_wheel(self, canvas: tk.Canvas) -> None:
        def on_enter(_e):
            if self._wheel_bound:
                return

            def wheel(e):
                if sys.platform == "darwin":
                    canvas.yview_scroll(int(-1 * e.delta), "units")
                else:
                    canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

            canvas.bind_all("<MouseWheel>", wheel)
            self._wheel_bound = True

        def on_leave(_e):
            if self._wheel_bound:
                canvas.unbind_all("<MouseWheel>")
                self._wheel_bound = False

        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)

    def create_widgets(self) -> None:
        header = ttk.Frame(self.root, padding=(12, 10, 12, 4))
        header.pack(fill=tk.X)
        ttk.Label(header, text="Chiplet 热仿真工作台", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(
            header,
            text="左侧填写或载入参数，右侧查看结果；悬停字段名可查看完整说明。命令行：python gui.py --cli --help",
            style="Subheader.TLabel",
        ).pack(anchor=tk.W, pady=(2, 0))

        paned = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        left_outer = ttk.Frame(paned, padding=4)
        right_outer = ttk.Frame(paned, padding=4)
        paned.add(left_outer, weight=3)
        paned.add(right_outer, weight=2)

        lf = ttk.LabelFrame(left_outer, text="参数", padding=(8, 8))
        lf.pack(fill=tk.BOTH, expand=True)

        btn_row = ttk.Frame(lf)
        btn_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(btn_row, text="▶ 分层模型", command=lambda: self.run_analysis(True)).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(btn_row, text="▶ 简单模型 (θ_JA)", command=lambda: self.run_analysis(False)).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(btn_row, text="恢复默认", command=self.reset_defaults).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btn_row, text="从 JSON 载入…", command=self.load_json).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btn_row, text="保存 JSON…", command=self.save_json).pack(side=tk.LEFT)

        canvas = tk.Canvas(lf, borderwidth=0, highlightthickness=0, bg="#fafafa")
        vsb = ttk.Scrollbar(lf, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas, style="Card.TFrame")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self._canvas_inner_win = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_canvas_configure(event):
            canvas.itemconfigure(self._canvas_inner_win, width=max(event.width - 4, 1))

        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._bind_canvas_wheel(canvas)

        inner.columnconfigure(1, weight=1)
        row = 0
        for spec in FORM_FIELDS:
            if spec.get("kind") == "section":
                sep = ttk.Separator(inner, orient=tk.HORIZONTAL)
                sep.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=(14, 6), padx=4)
                row += 1
                ttk.Label(inner, text=spec["title"], style="Section.TLabel").grid(
                    row=row, column=0, columnspan=3, sticky=tk.W, padx=4, pady=(0, 4)
                )
                row += 1
                continue

            fid = spec["id"]
            val = self._values.get(fid, spec["default"])

            lab = ttk.Label(inner, text=spec["label"] + (f"  ({spec['unit']})" if spec["unit"] else ""))
            lab.grid(row=row, column=0, sticky=tk.W, padx=(4, 8), pady=4)
            ToolTip(lab, spec["hint"])

            if spec.get("widget") == "check":
                var = tk.BooleanVar(value=bool(val))
                self._vars[fid] = var
                cb = ttk.Checkbutton(inner, variable=var)
                cb.grid(row=row, column=1, sticky=tk.W, pady=4)
                self._entries[fid] = cb
            else:
                ent = ttk.Entry(inner, width=18)
                ent.insert(0, str(val))
                ent.grid(row=row, column=1, sticky=tk.W, pady=4)
                self._entries[fid] = ent
                ToolTip(ent, spec["hint"])

            hint = ttk.Label(
                inner,
                text=spec["hint"][:140] + ("…" if len(spec["hint"]) > 140 else ""),
                style="Hint.TLabel",
            )
            hint.grid(row=row + 1, column=0, columnspan=3, sticky=tk.W, padx=(8, 4), pady=(0, 6))
            row += 2

        rf = ttk.LabelFrame(right_outer, text="结果", padding=(8, 8))
        rf.pack(fill=tk.BOTH, expand=True)
        res_btns = ttk.Frame(rf)
        res_btns.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(res_btns, text="导出 CSV…", command=self.export_csv).pack(side=tk.LEFT)

        self.result_text = scrolledtext.ScrolledText(
            rf,
            width=52,
            wrap=tk.NONE,
            font=("Menlo", 11) if sys.platform == "darwin" else ("Consolas", 10),
            bg="#1e1e2e",
            fg="#e8e8f0",
            insertbackground="#fff",
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)

    def read_form(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for spec in FORM_FIELDS:
            if spec.get("kind") == "section":
                continue
            fid = spec["id"]
            if spec.get("widget") == "check":
                out[fid] = bool(self._vars[fid].get())
            else:
                w = self._entries[fid]
                if not isinstance(w, ttk.Entry):
                    continue
                raw = w.get().strip()
                out[fid] = _parse_scalar(raw, spec["ptype"])
        return out

    def write_form(self, values: Dict[str, Any]) -> None:
        for spec in FORM_FIELDS:
            if spec.get("kind") == "section":
                continue
            fid = spec["id"]
            if fid not in values:
                continue
            if spec.get("widget") == "check":
                self._vars[fid].set(bool(values[fid]))
            else:
                w = self._entries[fid]
                if not isinstance(w, ttk.Entry):
                    continue
                w.delete(0, tk.END)
                w.insert(0, str(values[fid]))

    def reset_defaults(self) -> None:
        self._values = dict(self._defaults)
        self.write_form(self._values)

    def load_json(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if not path:
            return
        try:
            data = load_form_json(Path(path))
            self._values = merge_config_into_form(default_form_values(), data)
            self.write_form(self._values)
            messagebox.showinfo("载入", f"已载入：{path}")
        except Exception as e:
            messagebox.showerror("载入失败", str(e))

    def save_json(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile="chiplet_thermal_params.json",
        )
        if not path:
            return
        try:
            data = self.read_form()
            with open(path, "w", encoding="utf-8") as fp:
                json.dump(data, fp, indent=2, ensure_ascii=False)
            messagebox.showinfo("保存", f"已保存：{path}")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    def export_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="chiplet_thermal_results.csv",
        )
        if not path:
            return
        if self._last_df is None:
            messagebox.showwarning("导出", "请先运行一次分析。")
            return
        try:
            self._last_df.to_csv(path, index=False, encoding="utf-8-sig")
            messagebox.showinfo("导出", f"已写入：{path}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def run_analysis(self, hierarchical: bool) -> None:
        try:
            f = self.read_form()
            kw = form_values_to_analyze_kwargs(f, use_hierarchical=hierarchical)
            df = analyze_scaling(**kw)
            self._last_df = df
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, "── 当前表单参数（工程单位）──\n")
            for k in sorted(f.keys()):
                self.result_text.insert(tk.END, f"  {k}: {f[k]}\n")
            self.result_text.insert(tk.END, f"\n── 模型: {'分层物理热阻' if hierarchical else '简单 θ_JA'} ──\n\n")
            self.result_text.insert(tk.END, df.to_string(index=False))
            self.result_text.insert(tk.END, "\n")
        except Exception as e:
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, f"错误: {e}\n")
            messagebox.showerror("运行失败", str(e))


def _parse_chiplet_counts(s: str) -> List[int]:
    parts = [p.strip() for p in s.replace(";", ",").split(",") if p.strip()]
    return [int(p) for p in parts]


def build_cli_parser() -> argparse.ArgumentParser:
    epilog = """
示例:
  python gui.py --cli --chiplets 2,4,8 --hierarchical
  python gui.py --cli --config my.json -o out.csv
  python gui.py --config my.json
  # my.json 可含表单字段 id，以及可选 "chiplet_counts": [2,4]、"use_hierarchical": true
  # 以及任意 analyze_scaling 接受的英文关键字（如 "transistor_density": 150）。
"""
    p = argparse.ArgumentParser(
        description="Chiplet 热 / 功耗 / 面积：图形界面或命令行批跑 analyze_scaling。",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=epilog,
    )
    p.add_argument(
        "--cli",
        action="store_true",
        help="无图形界面，直接计算并在标准输出打印表格",
    )
    p.add_argument(
        "--config",
        type=Path,
        metavar="PATH",
        help="JSON：表单字段 id（与「保存 JSON」一致），可选 chiplet_counts 列表与 use_hierarchical；"
        "亦可包含 analyze_scaling 的其它关键字（与表单键合并后传入）。",
    )
    p.add_argument(
        "--chiplets",
        type=str,
        default="4",
        metavar="LIST",
        help="逗号分隔的 chiplet 数量扫描点，如 2,4,8（CLI 默认 4）",
    )
    p.add_argument(
        "--hierarchical",
        action="store_true",
        help="使用分层物理热阻模型",
    )
    p.add_argument(
        "--output",
        "-o",
        type=Path,
        metavar="CSV",
        help="将结果表写入 UTF-8 CSV",
    )
    p.add_argument("--target-fp16", type=float, dest="target_total_fp16", help="总算力目标 (TFLOPS)")
    p.add_argument("--ambient", type=float, dest="ambient_temp", help="环境温度 (°C)")
    p.add_argument("--theta-ja", type=float, dest="theta_ja", help="简单模型 θ_JA (°C/W)")
    return p


def build_analyze_kwargs_for_cli(args: argparse.Namespace) -> Dict[str, Any]:
    cfg: Dict[str, Any] = {}
    if args.config:
        cfg.update(load_form_json(args.config))
    if args.target_total_fp16 is not None:
        cfg["target_total_fp16"] = args.target_total_fp16
    if args.ambient_temp is not None:
        cfg["ambient_temp"] = args.ambient_temp
    if args.theta_ja is not None:
        cfg["theta_ja"] = args.theta_ja

    merged = merge_config_into_form(default_form_values(), cfg)
    counts: Optional[List[int]] = None
    if isinstance(cfg.get("chiplet_counts"), list):
        counts = [int(x) for x in cfg["chiplet_counts"]]
    else:
        counts = _parse_chiplet_counts(args.chiplets)

    use_hierarchical = bool(cfg.get("use_hierarchical", args.hierarchical))
    kw = form_values_to_analyze_kwargs(merged, chiplet_counts=counts, use_hierarchical=use_hierarchical)
    for key, val in cfg.items():
        if key in _ANALYZE_KEYS and val is not None and key not in _FORM_FIELD_IDS:
            kw[key] = val
    return kw


def run_cli(args: argparse.Namespace) -> int:
    kw = build_analyze_kwargs_for_cli(args)
    df = analyze_scaling(**kw)
    print(df.to_string(index=False))
    if args.output:
        df.to_csv(args.output, index=False, encoding="utf-8-sig")
        print(f"\n[已写入] {args.output}", file=sys.stderr)
    return 0


def launch_gui(initial: Optional[Dict[str, Any]] = None) -> None:
    root = tk.Tk()
    apply_theme(root)
    ThermalGUI(root, initial_values=initial)
    root.mainloop()


def main() -> int:
    args = build_cli_parser().parse_args()
    if args.cli:
        return run_cli(args)

    cfg_updates: Dict[str, Any] = {}
    if args.config:
        cfg_updates.update(load_form_json(args.config))
    if args.target_total_fp16 is not None:
        cfg_updates["target_total_fp16"] = args.target_total_fp16
    if args.ambient_temp is not None:
        cfg_updates["ambient_temp"] = args.ambient_temp
    if args.theta_ja is not None:
        cfg_updates["theta_ja"] = args.theta_ja
    if args.chiplets.strip() != "4":
        cfg_updates["chiplet_counts"] = _parse_chiplet_counts(args.chiplets)

    initial = merge_config_into_form(default_form_values(), cfg_updates) if cfg_updates else None
    launch_gui(initial)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
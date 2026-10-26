"""Publication-style figures for the reproducible results analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Any

INK = "#172D42"
MUTED = "#62758A"
BASE = "#91A5B9"
TRAINED = "#087F82"
NEGATIVE = "#BD6845"
GRID = "#E6EDF2"


def render_all(data: dict[str, Any], output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "text.color": INK,
            "axes.labelcolor": MUTED,
            "xtick.color": MUTED,
            "ytick.color": INK,
            "axes.titleweight": "bold",
            "axes.titlesize": 13,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": False,
            "axes.spines.bottom": False,
            "xtick.major.size": 0,
            "ytick.major.size": 0,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "svg.hashsalt": "invoiceops-rl-results",
            "savefig.facecolor": "white",
        }
    )
    output.mkdir(parents=True, exist_ok=True)

    def save(fig: Any, name: str) -> None:
        svg = output / f"{name}.svg"
        fig.savefig(
            svg,
            bbox_inches="tight",
            pad_inches=0.25,
            metadata={"Date": None, "Creator": "InvoiceOps reproducible analysis"},
        )
        svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
        fig.savefig(output / f"{name}.png", dpi=180, bbox_inches="tight", pad_inches=0.25)
        plt.close(fig)

    def header(fig: Any, eyebrow: str, title: str, subtitle: str) -> None:
        fig.text(0.055, 0.97, eyebrow, color=TRAINED, weight="bold", fontsize=10)
        fig.text(0.055, 0.91, title, weight="bold", fontsize=21)
        fig.text(0.055, 0.86, subtitle, color=MUTED, fontsize=11)

    def percent_axis(ax: Any) -> None:
        ax.set_ylim(0, 108)
        ax.set_yticks([0, 25, 50, 75, 100], labels=["0%", "25%", "50%", "75%", "100%"])
        ax.yaxis.grid(True, color=GRID)
        ax.set_axisbelow(True)

    # The requested initial-prompt → selected-prompt → RL comparison, with exact counts.
    fig, ax = plt.subplots(figsize=(12, 5.8))
    fig.subplots_adjust(left=0.085, right=0.965, top=0.71, bottom=0.2)
    header(
        fig,
        "THE EXPERIMENT  /  PROMPTING + DOMAIN-SPECIFIC RL",
        "From initial prompt to trained policy execution.",
        "The same 4B model family, evaluated on strict InvoiceOps task completion.",
    )
    percent_axis(ax)
    stages = data["prompting"]["stages"]
    colors = ["#C7D3DE", BASE, TRAINED]
    values = [100 * r["success"] for r in stages]
    ax.bar(range(3), values, width=0.5, color=colors)
    for i, _row in enumerate(stages):
        ax.text(
            i,
            values[i] + 2.5,
            f"{values[i]:.1f}%",
            ha="center",
            va="bottom",
            weight="bold",
            fontsize=20,
            color=TRAINED if i == 2 else INK,
        )
    ax.set_xticks(
        range(3),
        labels=[
            f"Initial prompt · v1\n{stages[0]['passes']} / 96 passes",
            f"Selected prompt · v3d\n{stages[1]['passes']} / 96 passes",
            f"Selected prompt + RL\n{stages[2]['passes']} / 96 passes",
        ],
    )
    ax.set_xlim(-0.7, 2.7)
    ax.annotate(
        "",
        xy=(0.96, 102),
        xytext=(0.04, 102),
        arrowprops={"arrowstyle": "->", "color": MUTED, "linewidth": 1.4},
    )
    ax.text(0.5, 104, "+71.9 pp · initial → selected prompt", ha="center", fontsize=11, color=MUTED)
    ax.text(1.95, 104, "+8.3 pp · RL", ha="center", fontsize=12, color=TRAINED, weight="bold")
    fig.text(
        0.055,
        0.075,
        "Selected-prompt baseline → RL: 20 failures → 12  ·  40% fewer observed failures",
        fontsize=12,
        color=TRAINED,
        weight="bold",
    )
    fig.text(
        0.055,
        0.025,
        "24 test tasks \u00d7 4 attempts per stage. "
        "Passes require a correct system state and action history.",
        fontsize=10,
        color=MUTED,
    )
    save(fig, "prompt-to-rl")

    # Primary outcomes: full 0-100% axes and paired-task bootstrap uncertainty.
    fig, axes = plt.subplots(1, 2, figsize=(12, 6.1))
    fig.subplots_adjust(left=0.075, right=0.975, top=0.72, bottom=0.18, wspace=0.27)
    header(
        fig,
        "INVOICEOPS  /  MATCHED MODEL COMPARISON",
        "More correct outcomes. More repeatable execution.",
        "Same 4B base, prompt, task data and decoding. Only the trained adapter changes.",
    )
    for ax, metric, title, counts in zip(
        axes,
        [data["invoiceops"]["primary"], data["invoiceops"]["pass_all_four"]],
        ["Strict policy success", "All four attempts succeed"],
        [("76 / 96 attempts", "84 / 96 attempts"), ("14 / 24 tasks", "18 / 24 tasks")],
        strict=True,
    ):
        percent_axis(ax)
        values = [100 * metric[k] for k in ("baseline", "trained")]
        intervals = [[100 * x for x in metric[k]] for k in ("baseline_ci95", "trained_ci95")]
        ax.bar([0, 1], values, color=[BASE, TRAINED], width=0.57, zorder=2)
        for i, (value, interval) in enumerate(zip(values, intervals, strict=True)):
            ax.errorbar(
                i,
                value,
                yerr=[[value - interval[0]], [interval[1] - value]],
                fmt="o",
                color=INK,
                capsize=5,
                markersize=4,
                linewidth=1.4,
                zorder=3,
            )
            ax.text(
                i,
                interval[1] + 2.3,
                f"{value:.1f}%",
                ha="center",
                va="bottom",
                weight="bold",
                fontsize=15,
                color=INK if i == 0 else TRAINED,
            )
        ax.set_xticks([0, 1], labels=[f"Untrained\n{counts[0]}", f"Trained\n{counts[1]}"])
        ax.set_xlim(-0.65, 1.65)
        ax.set_title(title, loc="left", pad=24)
        ax.text(
            0.99,
            1.07,
            f"+{metric['delta'] * 100:.1f} pp",
            transform=ax.transAxes,
            ha="right",
            weight="bold",
            color=TRAINED,
            fontsize=12,
        )
    fig.text(
        0.055,
        0.075,
        "20 failed attempts → 12  ·  40% fewer observed failures",
        fontsize=13,
        weight="bold",
        color=TRAINED,
    )
    fig.text(
        0.055,
        0.025,
        "Whiskers: 95% task-bootstrap intervals, 100,000 resamples. "
        "24 test tasks \u00d7 4 attempts.",
        fontsize=10,
        color=MUTED,
    )
    save(fig, "invoiceops-results")

    # Distribution of observed gains: all companies and all families, including declines.
    fig, (left, right) = plt.subplots(1, 2, figsize=(13, 7.2))
    fig.subplots_adjust(left=0.15, right=0.96, top=0.73, bottom=0.22, wspace=0.8)
    header(
        fig,
        "INVOICEOPS  /  WHERE THE GAINS APPEAR",
        "Improvement across companies and task families.",
        "Three company means increase; the fourth is unchanged. Six family means increase.",
    )
    companies = data["invoiceops"]["companies"]
    short_names = {
        "Glimmerdale Industrial Supply": "Glimmerdale",
        "Juniper Fold Logistics": "Juniper Fold",
        "Marrowind Energy Services": "Marrowind",
        "Pellucid Medical Components": "Pellucid",
    }
    for i, row in enumerate(companies):
        a, b = 100 * row["baseline"], 100 * row["trained"]
        left.plot([a, b], [i, i], color=TRAINED if b > a else BASE, linewidth=3, zorder=1)
        left.scatter(a, i, color=BASE, s=75, zorder=2, edgecolor="white")
        left.scatter(b, i, color=TRAINED, marker="s", s=60, zorder=3, edgecolor="white")
        left.text(b + 2, i, f"{b:.1f}%", va="center", color=TRAINED, weight="bold", fontsize=10)
        if b != a:
            left.text(a - 1, i + 0.22, f"{a:.1f}%", ha="right", color=MUTED, fontsize=10)
    names = [short_names.get(r["name"], r["name"].split()[0]) for r in companies]
    left.set_yticks(range(len(companies)), labels=names)
    left.set_xlim(0, 116)
    left.set_xticks([0, 25, 50, 75, 100], labels=["0%", "25%", "50%", "75%", "100%"])
    left.set_ylim(-0.6, 3.65)
    left.invert_yaxis()
    left.xaxis.grid(True, color=GRID)
    left.set_axisbelow(True)
    left.set_title("Company means · 24 attempts each", loc="left", pad=20)
    left.legend(
        handles=[
            Line2D([], [], marker="o", color=BASE, linestyle="", label="Untrained"),
            Line2D([], [], marker="s", color=TRAINED, linestyle="", label="Trained"),
        ],
        frameon=False,
        loc="upper left",
        bbox_to_anchor=(-0.2, -0.09),
        ncols=2,
    )
    families = data["invoiceops"]["families"]
    family_labels = [
        "F01  Clean match",
        "F02  Price discrepancy",
        "F03  Short receipt",
        "F04  Duplicate invoice",
        "F05  Credit note",
        "F06  Approval routing",
        "F07  Vendor conflict",
        "F08  Missing receipt",
        "F09  Shared PO capacity",
        "F10  Untrusted document*",
        "F11  Transient failure",
        "F12  Amended records",
    ]
    deltas = [100 * r["delta"] for r in families]
    right.barh(
        range(12),
        deltas,
        height=0.53,
        color=[TRAINED if d > 0 else NEGATIVE if d < 0 else BASE for d in deltas],
    )
    for i, delta in enumerate(deltas):
        right.text(
            delta + 1.4 if delta >= 0 else delta / 2,
            i,
            f"{delta:+.1f}" if delta else "0",
            ha="left" if delta >= 0 else "center",
            va="center",
            fontsize=10,
            color=TRAINED if delta > 0 else "white" if delta < 0 else MUTED,
        )
    right.set_yticks(range(12), labels=family_labels)
    right.invert_yaxis()
    right.set_xlim(-21, 46)
    right.set_xticks([-12.5, 0, 12.5, 25, 37.5])
    right.axvline(0, color=INK, linewidth=0.8)
    right.xaxis.grid(True, color=GRID)
    right.set_axisbelow(True)
    right.set_xlabel("Change in success (percentage points)", labelpad=10)
    right.set_title("Family means · 8 attempts each", loc="left", pad=20)
    fig.text(
        0.055,
        0.09,
        "Observed group means; each task retains all four attempts. Small groups are descriptive.",
        fontsize=10,
        color=MUTED,
    )
    fig.text(
        0.055,
        0.045,
        "*F10 attachments were not opened; the gain does not establish injection resistance.",
        fontsize=10,
        color=MUTED,
    )
    save(fig, "generalization")

    # External checks are prominent, complete and labelled as point estimates.
    fig, (left, right) = plt.subplots(1, 2, figsize=(13, 6.8))
    fig.subplots_adjust(left=0.075, right=0.955, top=0.72, bottom=0.22, wspace=0.72)
    header(
        fig,
        "EXTERNAL EVALUATION  /  NO EXTERNAL RL TRAINING",
        "Domain-specific RL, broader evaluation.",
        "Small positive τ² point estimates; general function-calling performance largely retained.",
    )
    percent_axis(left)
    metrics = [data["tau2"]["mean_reward"], data["tau2"]["pass_all_four"]]
    for i, metric in enumerate(metrics):
        for j, key in enumerate(("baseline", "trained")):
            x = i + (-0.18 if j == 0 else 0.18)
            value = 100 * metric[key]
            lo, hi = [100 * v for v in metric[f"{key}_ci95"]]
            left.bar(x, value, width=0.3, color=BASE if j == 0 else TRAINED)
            left.errorbar(
                x,
                value,
                yerr=[[value - lo], [hi - value]],
                fmt="none",
                color=INK,
                capsize=3,
                linewidth=1.1,
            )
            left.text(
                x,
                value - 7,
                f"{value:.1f}",
                ha="center",
                color=INK if j == 0 else "white",
                fontsize=10,
                weight="bold",
                zorder=5,
                bbox={"facecolor": BASE if j == 0 else TRAINED, "edgecolor": "none", "pad": 1.8},
            )
        left.text(
            i,
            max(100 * metric[k][1] for k in ("baseline_ci95", "trained_ci95")) + 4,
            f"+{metric['delta'] * 100:.2f} pp",
            ha="center",
            color=TRAINED,
            weight="bold",
        )
    left.set_xticks([0, 1], labels=["Mean reward", "All 4 trials"])
    left.set_xlim(-0.6, 1.6)
    left.set_title("τ² retail · 40 tasks \u00d7 4 trials", loc="left", pad=20)
    left.legend(
        handles=[
            Line2D([], [], color=BASE, linewidth=8, label="Untrained"),
            Line2D([], [], color=TRAINED, linewidth=8, label="Trained"),
        ],
        loc="upper left",
        frameon=False,
        ncols=2,
        fontsize=10,
    )
    bfcl = data["bfcl"]["categories"]
    labels = [
        "Simple Python",
        "Multiple",
        "Parallel",
        "Parallel multiple",
        "Irrelevance",
        "Live simple",
        "Live multiple",
        "Multi-turn base",
    ]
    changes = [100 * r["delta"] for r in bfcl]
    right.barh(
        range(8),
        changes,
        height=0.52,
        color=[TRAINED if x > 0 else NEGATIVE if x < 0 else BASE for x in changes],
    )
    for i, change in enumerate(changes):
        right.text(
            change + (0.06 if change >= 0 else -0.06),
            i,
            f"{change:+.2f}",
            va="center",
            ha="left" if change >= 0 else "right",
            fontsize=10,
            color=TRAINED if change > 0 else NEGATIVE if change < 0 else MUTED,
        )
    right.set_yticks(range(8), labels=labels)
    right.invert_yaxis()
    right.set_xlim(-2, 0.95)
    right.set_xticks([-1.5, -1, -0.5, 0, 0.5])
    right.axvline(0, color=INK, linewidth=0.8)
    right.xaxis.grid(True, color=GRID)
    right.set_axisbelow(True)
    right.set_xlabel("Change in accuracy (percentage points)", labelpad=10)
    right.set_title("BFCL · all 2,751 planned cases", loc="left", pad=20)
    fig.text(
        0.055,
        0.095,
        "τ²: paired-task 95% bootstrap intervals. Local customer model; ENV-only grading.",
        fontsize=10,
        color=MUTED,
    )
    fig.text(
        0.055,
        0.045,
        "BFCL: all eight categories shown. "
        "Custom executed-case accuracy: 80.48% → 80.37% (-3 cases).",
        fontsize=10,
        color=MUTED,
    )
    save(fig, "external-benchmarks")

    # Explicit uncertainty, with a visible zero line and the same units for every row.
    fig, ax = plt.subplots(figsize=(12, 5.5))
    fig.subplots_adjust(left=0.255, right=0.74, top=0.72, bottom=0.2)
    header(
        fig,
        "STATISTICAL ANALYSIS  /  PAIRED TASKS",
        "Effect sizes, with uncertainty kept visible.",
        "100,000 paired bootstrap resamples; "
        "both models and all trials stay together within a task.",
    )
    rows = [
        data["invoiceops"]["primary"],
        data["invoiceops"]["pass_all_four"],
        data["tau2"]["mean_reward"],
        data["tau2"]["pass_all_four"],
    ]
    names = ["InvoiceOps · success", "InvoiceOps · all four", "τ² · mean reward", "τ² · all four"]
    for i, row in enumerate(rows):
        value = 100 * row["delta"]
        low, high = [100 * v for v in row["delta_ci95"]]
        color = TRAINED if i < 2 else "#496CA4"
        ax.errorbar(
            value,
            i,
            xerr=[[value - low], [high - value]],
            fmt="o",
            color=color,
            markersize=8,
            capsize=5,
            linewidth=2,
        )
        ax.text(
            1.04,
            i,
            f"{value:+.2f} [{low:+.2f}, {high:+.2f}]",
            transform=ax.get_yaxis_transform(),
            va="center",
            fontsize=11,
            color=color,
        )
    ax.text(1.04, 1.10, "Δ and 95% interval (pp)", transform=ax.transAxes, color=MUTED, fontsize=10)
    ax.set_yticks(range(4), labels=names)
    ax.invert_yaxis()
    ax.set_ylim(3.6, -0.6)
    ax.set_xlim(-15, 42)
    ax.set_xticks([-10, 0, 10, 20, 30, 40])
    ax.axvline(0, linestyle="--", color=MUTED, linewidth=1)
    ax.xaxis.grid(True, color=GRID)
    ax.set_axisbelow(True)
    ax.set_xlabel("Trained - untrained (percentage points)", labelpad=12)
    fig.text(
        0.055,
        0.08,
        "All intervals include zero. Exact two-sided task test: p = 0.141; "
        "company sensitivity: p = 0.250.",
        fontsize=10,
        color=MUTED,
    )
    fig.text(
        0.055,
        0.035,
        "Exploratory estimates; the observed gains are not a claim of statistical significance.",
        fontsize=10,
        color=MUTED,
    )
    save(fig, "uncertainty")

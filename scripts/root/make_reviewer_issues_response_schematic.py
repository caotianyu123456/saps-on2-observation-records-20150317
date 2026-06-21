from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parent
FONT = font_manager.FontProperties(fname=r"C:\Windows\Fonts\simhei.ttf")


def text(ax, x, y, s, size=10, color="#222", ha="left", va="top", weight=None, **kwargs):
    ax.text(
        x,
        y,
        s,
        fontsize=size,
        color=color,
        ha=ha,
        va=va,
        fontproperties=FONT,
        fontweight=weight,
        linespacing=1.22,
        **kwargs,
    )


def box(ax, x, y, w, h, title, body, edge, fill, title_color, body_size=9.3):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.035,rounding_size=0.08",
        linewidth=1.8,
        edgecolor=edge,
        facecolor=fill,
    )
    ax.add_patch(patch)
    text(ax, x + 0.18, y + h - 0.20, title, size=10.8, color=title_color, weight="bold")
    if body:
        text(ax, x + 0.18, y + h - 0.62, body, size=body_size, color="#222")
    return patch


def arrow(ax, x1, y1, x2, y2, color="#777", lw=1.7, rad=0):
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle="-|>",
            mutation_scale=13,
            linewidth=lw,
            color=color,
            connectionstyle=f"arc3,rad={rad}",
            alpha=0.9,
        )
    )


def main():
    fig, ax = plt.subplots(figsize=(16, 9), dpi=220)
    fig.patch.set_facecolor("#fbfbfb")
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis("off")

    red, red_fill = "#b84a4a", "#fff1f1"
    orange, orange_fill = "#c77700", "#fff7e8"
    blue, blue_fill = "#2f6f9f", "#eef7ff"
    green, green_fill = "#2e7d55", "#edf8f1"

    text(ax, 8, 8.68, "审稿主要问题与对应回复策略", size=20, ha="center", va="center", weight="bold")
    text(
        ax,
        8,
        8.30,
        "把分散质疑收束到一个可验证核心：SAPS 是否造成 O/N2 降低，并通过成分变化调制 630.0 nm 发光",
        size=12.5,
        ha="center",
        va="center",
        color="#333",
    )

    box(ax, 0.55, 7.55, 4.3, 0.45, "审稿人的主要质疑", "", red, "#ffe9e9", red)
    box(ax, 5.55, 7.55, 4.9, 0.45, "共同症结：机制链条缺少可见证据", "", orange, "#fff0d2", orange)
    box(ax, 11.1, 7.55, 4.35, 0.45, "对应回复与补充材料", "", blue, "#e6f2ff", blue)

    left = [
        (
            "1. 空间错位",
            "red-line 增强、极光沉降、\nSAPS channel / poleward edge\n的位置关系没有被直接展示。",
        ),
        (
            "2. “电离增强”被误读",
            "审稿人理解成 total ionization 增强，\n因此追问 GLOW 输入、electron flux、\ncolumn-integrated ionization。",
        ),
        (
            "3. 缺少观测验证",
            "只有 SAPS empirical model +\nTIEGCM + GLOW，不足以支撑\n关键物理结论。",
        ),
        (
            "4. SAPS 是否直接激发",
            "SAPS 离子流不能直接电离中性大气；\n更合理的表述是调制已有\n极光边缘/亚极光发光。",
        ),
    ]
    yvals = [6.50, 5.28, 4.06, 2.84]
    for (title, body), y in zip(left, yvals):
        box(ax, 0.55, y, 4.3, 0.96, title, body, red, red_fill, red, body_size=8.7)

    box(
        ax,
        5.55,
        5.88,
        4.9,
        1.46,
        "需要厘清的相对关系",
        "背景电离主要由极光沉降提供；\nSAPS 主要改变成分，使 O/N2 降低、\n分子成分相对增加；\n需要说明两者如何在空间上相邻或部分重合。",
        orange,
        orange_fill,
        orange,
        body_size=8.7,
    )
    box(
        ax,
        5.55,
        4.18,
        4.9,
        1.22,
        "为什么聚焦 O/N2 观测",
        "O/N2 是机制里最关键、最可观测的一环；\n它检验 composition depletion，\n而不是陷入 total ionization 或 auroral flux 的争论。",
        orange,
        orange_fill,
        orange,
        body_size=8.7,
    )
    box(
        ax,
        5.55,
        2.86,
        4.9,
        0.82,
        "收束后的主张",
        "SAPS 不是直接“激发”SAR arc，\n而是通过成分变化调制 SAR-arc-like red-line emission。",
        orange,
        orange_fill,
        orange,
        body_size=8.7,
    )

    right = [
        (
            "A. 改论文主张",
            "从 direct excitation 改为：\nSAPS-modulated 630.0 nm enhancement。",
        ),
        (
            "B. 补 O/N2 观测",
            "TIMED/GUVI：17 Mar 相对 16 Mar，\nSAPS 相关 LT/地理扇区存在\nstorm-time O/N2 depletion。",
        ),
        (
            "C. 厘清背景电离与 SAPS 关系",
            "并列展示：background ionization、\nSAPS-related O/N2 decrease、\n以及最终 630.0 nm enhancement 的相对位置。",
        ),
        (
            "D. DMSP 作为辅助",
            "ion drift 说明 SAPS-like flow 存在；\n但要明确时空限制，不能把非同步轨道\n当作 9 UT 严格验证。",
        ),
    ]
    for (title, body), y in zip(right, yvals):
        box(ax, 11.1, y, 4.35, 0.96, title, body, blue, blue_fill, blue, body_size=8.7)

    for y in [6.98, 5.76, 4.54, 3.32]:
        arrow(ax, 4.85, y, 5.55, 4.80, color="#a87420", lw=1.3, rad=0.08)

    arrow(ax, 10.45, 6.62, 11.10, 6.98, color=green, lw=1.6)
    arrow(ax, 10.45, 4.78, 11.10, 5.76, color=green, lw=1.6)
    arrow(ax, 10.45, 4.78, 11.10, 4.54, color=green, lw=1.6)
    arrow(ax, 10.45, 3.20, 11.10, 3.32, color=green, lw=1.6)

    box(
        ax,
        0.85,
        0.76,
        14.35,
        1.20,
        "统一回复口径",
        "我们并不主张 SAPS 直接产生额外总电离或直接激发 SAR arc；我们主张 SAPS 通过成分扰动降低 O/N2，\n在已有极光电离背景附近改变分子离子化与复合过程，从而调制 630.0 nm emission。\n因此，O/N2 observation 是验证 composition-control mechanism 的关键证据。",
        green,
        green_fill,
        green,
        body_size=9.2,
    )

    box(
        ax,
        5.65,
        0.18,
        4.7,
        0.36,
        "最重要的补强：O/N2 observation + background ionization/SAPS relation",
        "",
        green,
        "#def3e6",
        green,
        body_size=8.5,
    )

    out_png = ROOT / "reviewer_issues_response_schematic.png"
    out_pdf = ROOT / "reviewer_issues_response_schematic.pdf"
    fig.savefig(out_png, bbox_inches="tight", facecolor=fig.get_facecolor())
    fig.savefig(out_pdf, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(out_png)
    print(out_pdf)


if __name__ == "__main__":
    main()

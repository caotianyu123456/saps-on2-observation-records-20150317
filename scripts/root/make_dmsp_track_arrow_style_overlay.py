from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from make_dmsp_track_arrow_overlay import read_dmsp_csv, select_near_9ut_passes, to_cols
from make_dmsp_on2_overlay import GUVI_16, GUVI_17, add_boxes, read_guvi_grid, sort_grid_by_lt


ROOT = Path(__file__).resolve().parent


def main():
    rows = []
    for path in [
        ROOT / "dmsp_f17_ssies_20150317_parsed.csv",
        ROOT / "dmsp_f18_ssies_20150317_parsed.csv",
    ]:
        rows.extend(read_dmsp_csv(path))
    cols = to_cols(rows)

    lon, lat, on2_17 = read_guvi_grid(GUVI_17)
    _, _, on2_16 = read_guvi_grid(GUVI_16)
    delta = on2_17 - on2_16
    lt, delta_lt = sort_grid_by_lt(lon, delta)
    focus = (lt >= 17) & (lt <= 24)

    passes = select_near_9ut_passes(cols)
    fig, ax = plt.subplots(figsize=(10.8, 5.8), dpi=220)

    bg = ax.pcolormesh(
        lt[focus],
        lat,
        delta_lt[:, focus],
        shading="auto",
        cmap="RdBu_r",
        vmin=-0.8,
        vmax=0.8,
    )
    cbar = fig.colorbar(bg, ax=ax, pad=0.012)
    cbar.set_label("GUVI O/N2 anomaly (17 Mar - 16 Mar)")
    add_boxes(ax)

    purple = "#7a1688"
    track_colors = {"F17": "#6f007f", "F18": "#8a2396"}
    arrow_scale = 0.43  # LT hours per 1000 m/s

    for item in passes:
        sat = item["sat"]
        track_mask = (
            (cols["satellite"] == sat)
            & (cols["ut"] >= item["t0"] - 0.08)
            & (cols["ut"] <= item["t1"] + 0.08)
            & (cols["glat"] >= 35)
            & (cols["glat"] <= 75)
            & (cols["lt9"] >= 17)
            & (cols["lt9"] <= 24.1)
        )
        idx = np.where(track_mask)[0]
        idx = idx[np.argsort(cols["ut"][idx])]
        if len(idx) == 0:
            continue

        ax.plot(
            cols["lt9"][idx],
            cols["glat"][idx],
            color=track_colors.get(sat, purple),
            lw=2.4,
            alpha=0.96,
            zorder=5,
        )

        in_box = idx[
            (cols["glat"][idx] >= 40)
            & (cols["glat"][idx] <= 70)
            & (cols["lt9"][idx] >= 18)
            & (cols["lt9"][idx] <= 24)
        ]
        arrow_idx = in_box[::38]
        if len(arrow_idx) > 16:
            arrow_idx = arrow_idx[np.linspace(0, len(arrow_idx) - 1, 16, dtype=int)]

        drift = cols["horizontal_ion_drift_mps"][arrow_idx]
        # Positive horizontal DMSP drift is drawn westward, matching SAPS westward-flow convention.
        u = -drift / 1000.0 * arrow_scale
        v = np.zeros_like(u)
        speed = np.abs(drift)
        widths = 0.0048 + 0.0025 * np.clip(speed / 1800.0, 0, 1)
        for x0, y0, du, dv, width in zip(cols["lt9"][arrow_idx], cols["glat"][arrow_idx], u, v, widths):
            ax.quiver(
                x0,
                y0,
                du,
                dv,
                angles="xy",
                scale_units="xy",
                scale=1,
                color=purple,
                width=width,
                headwidth=5.2,
                headlength=6.4,
                headaxislength=5.4,
                pivot="middle",
                zorder=7,
            )

        if len(idx):
            mid = idx[len(idx) // 2]
            label_offsets = {
                ("F18", 7.57): (0.08, -1.2),
                ("F17", 8.00): (-0.18, 0.8),
                ("F18", 9.27): (0.10, 1.0),
            }
            key = (sat, round(item["t0"], 2))
            dx, dy = label_offsets.get(key, (0.08, 0.0))
            ax.text(
                cols["lt9"][mid] + dx,
                cols["glat"][mid] + dy,
                f"{sat} {item['t0']:.2f}-{item['t1']:.2f} UT",
                color=purple,
                fontsize=9.2,
                ha="left" if dx >= 0 else "right",
                va="center",
                bbox=dict(fc="white", ec="none", alpha=0.72, pad=1.5),
                zorder=8,
            )

    ax.quiver(
        21.85,
        37.6,
        arrow_scale,
        0,
        angles="xy",
        scale_units="xy",
        scale=1,
        color=purple,
        width=0.0072,
        headwidth=5.2,
        headlength=6.4,
        headaxislength=5.4,
        pivot="middle",
        zorder=8,
    )
    ax.text(22.18, 37.6, "1000 m/s", color="black", fontsize=9.5, va="center", ha="left")

    ax.set_xlim(17, 24)
    ax.set_ylim(35, 75)
    ax.set_xticks(np.arange(17, 25, 1))
    ax.set_xlabel("Geographic longitude converted to LT at 9 UT (hours)")
    ax.set_ylabel("Geographic latitude (deg)")
    ax.set_title("DMSP ion-drift velocity arrows along satellite tracks")
    ax.grid(alpha=0.22)
    ax.text(
        0.02,
        0.98,
        "Purple curves: DMSP SSIES tracks crossing the subauroral sector near 9 UT.\n"
        "Purple arrows: horizontal ion drift along the track; arrow length scales with speed.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        bbox=dict(fc="white", ec="0.45", alpha=0.84, boxstyle="round,pad=0.32"),
        zorder=9,
    )
    fig.tight_layout()
    out = ROOT / "guvi_on2_dmsp_track_velocity_arrows_style.png"
    fig.savefig(out)
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    main()

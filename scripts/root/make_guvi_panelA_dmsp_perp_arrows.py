from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from make_dmsp_on2_overlay import GUVI_16, GUVI_17, read_guvi_grid, sort_grid_by_lt
from make_dmsp_track_arrow_overlay import read_dmsp_csv, select_near_9ut_passes, to_cols


ROOT = Path(__file__).resolve().parent


def draw_sector_boxes(ax, y0=40, y1=70):
    ax.plot([18, 24, 24, 18, 18], [y0, y0, y1, y1, y0], color="#ff7f0e", lw=2.0, ls="--")
    ax.plot([19, 23, 23, 19, 19], [y0, y0, y1, y1, y0], color="#d62728", lw=2.0)
    ax.axvline(21, color="k", lw=1.0, ls=":", alpha=0.9)
    ax.text(21, y1 + 2.8, "21 LT", ha="center", va="bottom", fontsize=9)


def local_track_normals(x, y):
    dx = np.gradient(x)
    dy = np.gradient(y)
    norm = np.hypot(dx, dy)
    norm[norm == 0] = np.nan
    tx = dx / norm
    ty = dy / norm
    # Rotate local tangent by +90 degrees. SSIES horizontal drift is cross-track,
    # so arrows are plotted normal to the projected satellite track.
    nx = -ty
    ny = tx
    return nx, ny


def add_track_arrows(ax, cols, passes):
    purple = "#7a1688"
    track_colors = {"F17": "#6f007f", "F18": "#8a2396"}
    # Length in plot units for a 1000 m/s drift. This is visual scaling,
    # not a conversion from m/s to geographic degrees.
    scale = 1.15

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
        if len(idx) < 4:
            continue

        x = cols["lt9"][idx]
        y = cols["glat"][idx]
        ax.plot(x, y, color=track_colors.get(sat, purple), lw=2.3, alpha=0.96, zorder=6)

        nx, ny = local_track_normals(x, y)
        in_box_pos = np.where((y >= 40) & (y <= 70) & (x >= 18) & (x <= 24))[0]
        arrow_pos = in_box_pos[::36]
        if len(arrow_pos) > 17:
            arrow_pos = arrow_pos[np.linspace(0, len(arrow_pos) - 1, 17, dtype=int)]

        for pos in arrow_pos:
            drift = cols["horizontal_ion_drift_mps"][idx[pos]]
            if not np.isfinite(drift) or not np.isfinite(nx[pos]) or not np.isfinite(ny[pos]):
                continue
            speed = abs(drift)
            length = (speed / 1000.0) * scale
            # Plot all speed arrows on the same side of each track; length
            # represents speed magnitude, not the drift sign.
            if nx[pos] < 0:
                nx[pos] *= -1
                ny[pos] *= -1
            width = 0.0022
            ax.quiver(
                x[pos],
                y[pos],
                nx[pos] * length,
                ny[pos] * length,
                angles="xy",
                scale_units="xy",
                scale=1,
                color=purple,
                width=width,
                headwidth=3.6,
                headlength=4.4,
                headaxislength=3.8,
                pivot="tail",
                zorder=8,
            )

        mid = idx[len(idx) // 2]
        label_offsets = {
            ("F18", 7.57): (0.10, -1.5),
            ("F17", 8.00): (-0.18, 0.8),
            ("F18", 9.27): (0.10, 1.0),
        }
        dx, dy = label_offsets.get((sat, round(item["t0"], 2)), (0.08, 0))
        ax.text(
            cols["lt9"][mid] + dx,
            cols["glat"][mid] + dy,
            f"{sat} {item['t0']:.2f}-{item['t1']:.2f} UT",
            color=purple,
            fontsize=8.5,
            ha="left" if dx >= 0 else "right",
            va="center",
            bbox=dict(fc="white", ec="none", alpha=0.72, pad=1.4),
            zorder=9,
        )

    # Scale arrow, drawn perpendicular-looking but placed in the free lower-right area.
    ax.quiver(
        21.0,
        -68,
        scale,
        0,
        angles="xy",
        scale_units="xy",
        scale=1,
        color=purple,
        width=0.0022,
        headwidth=3.6,
        headlength=4.4,
        headaxislength=3.8,
        pivot="tail",
        zorder=8,
    )
    ax.text(22.25, -68, "1000 m/s", color="black", fontsize=9, va="center", ha="left")


def main():
    rows = []
    for path in [
        ROOT / "dmsp_f17_ssies_20150317_parsed.csv",
        ROOT / "dmsp_f18_ssies_20150317_parsed.csv",
    ]:
        rows.extend(read_dmsp_csv(path))
    cols = to_cols(rows)
    passes = select_near_9ut_passes(cols)

    lon, lat, on2_17 = read_guvi_grid(GUVI_17)
    _, _, on2_16 = read_guvi_grid(GUVI_16)
    lt, on2_lt = sort_grid_by_lt(lon, on2_17)
    _, delta_lt = sort_grid_by_lt(lon, on2_17 - on2_16)

    fig, ax = plt.subplots(figsize=(13.2, 5.0), dpi=220)
    mesh = ax.pcolormesh(lt, lat, on2_lt, shading="auto", cmap="viridis", vmin=0, vmax=1.1)
    cbar = fig.colorbar(mesh, ax=ax, pad=0.012)
    cbar.set_label("O/N2")

    draw_sector_boxes(ax)
    add_track_arrows(ax, cols, passes)

    ax.text(
        12.0,
        52,
        "SAPS-related sector\nfrom model focus\n9 UT, 18-24 LT",
        ha="center",
        va="center",
        fontsize=9,
        bbox=dict(fc="white", ec="0.55", alpha=0.88, boxstyle="round,pad=0.28"),
    )
    ax.text(
        0.35,
        -73.0,
        "Orange dashed: 9 UT 18-24 LT sector; red: core SAPS analysis sector.\n"
        "Purple curves/arrows: DMSP SSIES tracks and cross-track horizontal ion drift; arrow length scales with speed.",
        ha="left",
        va="bottom",
        fontsize=8,
        bbox=dict(fc="white", ec="0.65", alpha=0.82, boxstyle="round,pad=0.28"),
    )

    ax.set_xlim(0, 24)
    ax.set_ylim(-80, 80)
    ax.set_xticks(np.arange(0, 25, 3))
    ax.set_xlabel("Local time at 9 UT (hour)")
    ax.set_ylabel("Geographic latitude (deg)")
    ax.set_title("TIMED/GUVI O/N2 on 17 March 2015 with DMSP ion-drift tracks")
    ax.grid(alpha=0.22)
    fig.tight_layout()

    out = ROOT / "guvi_on2_panelA_dmsp_perpendicular_arrows.png"
    fig.savefig(out)
    plt.close(fig)
    print(out)

    fig, axes = plt.subplots(2, 1, figsize=(13.2, 9.2), dpi=220, sharex=True)
    ax = axes[0]
    mesh = ax.pcolormesh(lt, lat, on2_lt, shading="auto", cmap="viridis", vmin=0, vmax=1.1)
    cbar = fig.colorbar(mesh, ax=ax, pad=0.012)
    cbar.set_label("O/N2")
    draw_sector_boxes(ax)
    add_track_arrows(ax, cols, passes)
    ax.text(
        12.0,
        52,
        "SAPS-related sector\nfrom model focus\n9 UT, 18-24 LT",
        ha="center",
        va="center",
        fontsize=9,
        bbox=dict(fc="white", ec="0.55", alpha=0.88, boxstyle="round,pad=0.28"),
    )
    ax.set_ylim(-80, 80)
    ax.set_ylabel("Geographic latitude (deg)")
    ax.set_title("A. TIMED/GUVI gridded O/N2 on 17 March 2015 with DMSP ion-drift tracks")
    ax.grid(alpha=0.22)

    ax = axes[1]
    mesh = ax.pcolormesh(lt, lat, delta_lt, shading="auto", cmap="RdBu_r", vmin=-0.8, vmax=0.8)
    cbar = fig.colorbar(mesh, ax=ax, pad=0.012)
    cbar.set_label("Delta O/N2")
    draw_sector_boxes(ax)
    ax.text(
        0.65,
        7.0,
        "Core sector (19-23 LT, 40-70N):\n"
        "16 Mar median O/N2 = 0.846\n"
        "17 Mar median O/N2 = 0.166\n"
        "Median change = -0.681\n"
        "Relative change = -80.4%",
        ha="left",
        va="bottom",
        fontsize=8.4,
        bbox=dict(fc="white", ec="0.55", alpha=0.88, boxstyle="round,pad=0.3"),
    )
    ax.set_xlim(0, 24)
    ax.set_ylim(0, 80)
    ax.set_xticks(np.arange(0, 25, 3))
    ax.set_xlabel("Local time at 9 UT (hour)")
    ax.set_ylabel("Geographic latitude (deg)")
    ax.set_title("B. O/N2 anomaly relative to 16 March 2015 (17 Mar minus 16 Mar)")
    ax.grid(alpha=0.22)

    fig.suptitle("Observed storm-time O/N2 depletion with DMSP ion-drift observations", y=0.985, fontsize=14)
    fig.text(
        0.015,
        0.012,
        "Longitude has been converted to local time using LT = 9 UT + longitude/15. "
        "Purple arrows in panel A are perpendicular to the DMSP track and scaled by horizontal ion-drift speed.",
        ha="left",
        va="bottom",
        fontsize=8,
    )
    fig.tight_layout(rect=[0, 0.025, 1, 0.965])
    out2 = ROOT / "guvi_on2_global_lt_panelA_dmsp_perpendicular_arrows.png"
    fig.savefig(out2)
    plt.close(fig)
    print(out2)


if __name__ == "__main__":
    main()

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from make_dmsp_on2_overlay import GUVI_16, GUVI_17, read_guvi_grid, sort_grid_by_lt


ROOT = Path(__file__).resolve().parent


SELECTED_PASSES = [
    # satellite, UT start inside the target box, UT end inside the target box
    ("F17", 20.21, 20.36),
    ("F18", 19.79, 19.93),
]


def read_rows():
    rows = []
    for path in [
        ROOT / "dmsp_f17_ssies_20150317_parsed.csv",
        ROOT / "dmsp_f18_ssies_20150317_parsed.csv",
    ]:
        with open(path, newline="") as handle:
            for row in csv.DictReader(handle):
                parsed = {"satellite": row["satellite"], "time_iso": row["time_iso"]}
                for key, value in row.items():
                    if key not in parsed:
                        parsed[key] = float(value)
                rows.append(parsed)
    return rows


def to_cols(rows):
    cols = {}
    for key in rows[0]:
        if key in {"satellite", "time_iso"}:
            cols[key] = np.array([row[key] for row in rows])
        else:
            cols[key] = np.array([row[key] for row in rows], dtype=float)
    return cols


def draw_boxes(ax):
    ax.plot([18, 24, 24, 18, 18], [40, 40, 70, 70, 40], color="#ff7f0e", lw=2.0, ls="--")
    ax.plot([19, 23, 23, 19, 19], [40, 40, 70, 70, 40], color="#d62728", lw=2.0)
    ax.axvline(21, color="k", lw=1.0, ls=":", alpha=0.9)
    ax.text(21, 73, "21 LT", ha="center", va="bottom", fontsize=9)


def add_screen_arrow(ax, x, y, normal_display, speed_mps, ref_px=32, color="#7a1688"):
    speed = abs(speed_mps)
    length_px = ref_px * speed / 1000.0
    if length_px < 2:
        return
    start_disp = ax.transData.transform((x, y))
    end_disp = start_disp + normal_display * length_px
    end_data = ax.transData.inverted().transform(end_disp)
    ax.annotate(
        "",
        xy=end_data,
        xytext=(x, y),
        arrowprops=dict(
            arrowstyle="-|>",
            color=color,
            lw=0.35,
            mutation_scale=3.2,
            shrinkA=0,
            shrinkB=0,
        ),
        zorder=8,
    )


def add_perpendicular_track_arrows(ax, cols):
    purple = "#7a1688"
    track_colors = {"F17": "#6f007f", "F18": "#8a2396"}
    ref_px = 20

    for sat, t0, t1 in SELECTED_PASSES:
        mask = (
            (cols["satellite"] == sat)
            & (cols["ut"] >= t0 - 0.50)
            & (cols["ut"] <= t1 + 0.50)
            & (cols["lt9"] >= 17)
            & (cols["lt9"] <= 24.05)
            & (cols["glat"] >= -15)
            & (cols["glat"] <= 82)
        )
        idx = np.where(mask)[0]
        idx = idx[np.argsort(cols["ut"][idx])]
        if len(idx) < 6:
            continue

        x = cols["lt9"][idx]
        y = cols["glat"][idx]
        drift = cols["horizontal_ion_drift_mps"][idx]
        ax.plot(x, y, color=track_colors.get(sat, purple), lw=2.2, alpha=0.95, zorder=6)

        # Normals are computed in display coordinates so arrows look perpendicular
        # on the final plotted map, not merely in raw x/y data units.
        xy_disp = ax.transData.transform(np.column_stack([x, y]))
        tangent = np.gradient(xy_disp, axis=0)
        norm = np.hypot(tangent[:, 0], tangent[:, 1])
        good = norm > 0
        tangent[good] /= norm[good, None]
        normals = np.column_stack([-tangent[:, 1], tangent[:, 0]])
        flip = normals[:, 0] < 0
        normals[flip] *= -1

        arrow_positions = np.arange(12, len(idx) - 12, 24)
        for pos in arrow_positions:
            add_screen_arrow(ax, x[pos], y[pos], normals[pos], drift[pos], ref_px=ref_px, color=purple)

        mid = idx[len(idx) // 2]
        label_offsets = {
            ("F17", 20.21): (-0.35, -2.5, "right"),
            ("F18", 19.79): (0.10, -2.3, "left"),
        }
        dx, dy, ha = label_offsets.get((sat, round(t0, 2)), (0.1, 0.0, "left"))
        ax.text(
            cols["lt9"][mid] + dx,
            cols["glat"][mid] + dy,
            f"{sat} {t0:.2f}-{t1:.2f} UT",
            color=purple,
            fontsize=8.2,
            ha=ha,
            va="center",
            bbox=dict(fc="white", ec="none", alpha=0.72, pad=1.2),
            zorder=9,
        )

    # Reference arrow with the same visual length scale.
    x0, y0 = 20.8, -68
    start_disp = ax.transData.transform((x0, y0))
    end_disp = start_disp + np.array([ref_px, 0.0])
    end_data = ax.transData.inverted().transform(end_disp)
    ax.annotate(
        "",
        xy=end_data,
        xytext=(x0, y0),
        arrowprops=dict(arrowstyle="-|>", color=purple, lw=0.35, mutation_scale=3.2, shrinkA=0, shrinkB=0),
        zorder=8,
    )
    ax.text(end_data[0] + 0.08, y0, "1000 m/s", color="black", fontsize=8.6, va="center", ha="left")


def main():
    rows = read_rows()
    cols = to_cols(rows)
    lon, lat, on2_17 = read_guvi_grid(GUVI_17)
    _, _, on2_16 = read_guvi_grid(GUVI_16)
    lt, on2_lt = sort_grid_by_lt(lon, on2_17)
    _, delta_lt = sort_grid_by_lt(lon, on2_17 - on2_16)

    fig, axes = plt.subplots(2, 1, figsize=(13.2, 9.2), dpi=220, sharex=True)
    ax = axes[0]
    mesh = ax.pcolormesh(lt, lat, on2_lt, shading="auto", cmap="viridis", vmin=0, vmax=1.1)
    cbar = fig.colorbar(mesh, ax=ax, pad=0.012)
    cbar.set_label("O/N2")
    draw_boxes(ax)
    ax.set_xlim(0, 24)
    ax.set_ylim(-80, 84)
    ax.set_ylabel("Geographic latitude (deg)")
    ax.set_title("A. TIMED/GUVI gridded O/N2 on 17 March 2015 with DMSP ion-drift tracks")
    ax.grid(alpha=0.22)
    ax.text(
        12.0,
        52,
        "SAPS-related sector\nfrom model focus\n9 UT, 18-24 LT",
        ha="center",
        va="center",
        fontsize=9,
        bbox=dict(fc="white", ec="0.55", alpha=0.88, boxstyle="round,pad=0.28"),
    )

    # Draw once so data/display transforms are final before computing perpendicular arrows.
    fig.canvas.draw()
    add_perpendicular_track_arrows(ax, cols)

    ax = axes[1]
    mesh = ax.pcolormesh(lt, lat, delta_lt, shading="auto", cmap="RdBu_r", vmin=-0.8, vmax=0.8)
    cbar = fig.colorbar(mesh, ax=ax, pad=0.012)
    cbar.set_label("Delta O/N2")
    draw_boxes(ax)
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

    fig.suptitle("Observed O/N2 depletion and DMSP ion-drift peaks in the SAPS sector", y=0.985, fontsize=14)
    fig.text(
        0.015,
        0.012,
        "Longitude has been converted to local time using LT = 9 UT + longitude/15. "
        "Panel A shows selected DMSP overpasses crossing the SAPS sector and adjacent latitudes; "
        "thin perpendicular arrows scale with |horizontal ion drift|.",
        ha="left",
        va="bottom",
        fontsize=8,
    )
    fig.subplots_adjust(left=0.065, right=0.94, top=0.92, bottom=0.06, hspace=0.18)

    out = ROOT / "guvi_on2_dmsp_peak_passes_perpendicular_arrows.png"
    fig.savefig(out)
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    main()

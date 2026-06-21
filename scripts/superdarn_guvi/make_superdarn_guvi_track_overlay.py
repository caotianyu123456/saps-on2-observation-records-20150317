from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
from PIL import Image

from make_guvi_dmsp_mlt_candidate import GUVI_FILES
from make_guvi_dmsp_westward_saps_window import read_guvi_raw_cd


ROOT = Path(__file__).resolve().parent

# The SuperDARN Canada quick-look PNG is a rendered polar MLT/MLAT map.
# These centers/radii are measured from the 1800 x 2400 archive image layout.
PANEL_LAYOUT = [
    {"center": (392.0, 397.0), "radius": 277.0, "window": (22 + 30 / 60, 22 + 32 / 60)},
    {"center": (1208.0, 397.0), "radius": 277.0, "window": (22 + 32 / 60, 22 + 34 / 60)},
    {"center": (392.0, 1165.0), "radius": 277.0, "window": (22 + 34 / 60, 22 + 36 / 60)},
    {"center": (1208.0, 1165.0), "radius": 277.0, "window": (22 + 36 / 60, 22 + 38 / 60)},
    {"center": (800.0, 1934.0), "radius": 277.0, "window": (22 + 38 / 60, 22 + 40 / 60)},
]


def mlat_mlt_to_pixels(mlat, mlt, center, radius):
    abs_mlat = np.abs(np.asarray(mlat, dtype=float))
    mlt = np.asarray(mlt, dtype=float)
    rho = (90.0 - abs_mlat) / 40.0 * radius
    theta = 2.0 * np.pi * (mlt - 6.0) / 24.0
    x = center[0] + rho * np.cos(theta)
    y = center[1] - rho * np.sin(theta)
    return x, y


def split_large_jumps(x, y, max_jump=70.0):
    if len(x) == 0:
        return []
    groups = []
    start = 0
    for i in range(1, len(x)):
        if np.hypot(x[i] - x[i - 1], y[i] - y[i - 1]) > max_jump:
            groups.append((x[start:i], y[start:i]))
            start = i
    groups.append((x[start:], y[start:]))
    return groups


def main():
    image_path = ROOT / "convection_maps_s_20150317_223800.png"
    if not image_path.exists():
        raise FileNotFoundError(f"Missing {image_path.name}; download it from the SuperDARN archive first.")

    guvi = read_guvi_raw_cd(GUVI_FILES["17 Mar"])
    image = np.asarray(Image.open(image_path).convert("RGB"))
    height, width = image.shape[:2]

    fig, ax = plt.subplots(figsize=(width / 180, height / 180), dpi=180)
    ax.imshow(image, extent=(0, width, height, 0))
    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)
    ax.axis("off")

    total_mask = np.zeros_like(guvi["ut"], dtype=bool)
    panel_counts = []
    for panel in PANEL_LAYOUT:
        start, end = panel["window"]
        mask = (
            (guvi["ut"] >= start)
            & (guvi["ut"] < end)
            & (guvi["mlat"] <= -50.0)
            & (guvi["mlat"] >= -80.0)
        )
        total_mask |= mask
        panel_counts.append(int(mask.sum()))
        if not np.any(mask):
            continue

        idx = np.where(mask)[0]
        idx = idx[np.argsort(guvi["ut"][idx])]
        x, y = mlat_mlt_to_pixels(guvi["mlat"][idx], guvi["mlt"][idx], panel["center"], panel["radius"])
        for xs, ys in split_large_jumps(x, y):
            if len(xs) < 2:
                continue
            ax.plot(
                xs,
                ys,
                color="#ffe66d",
                lw=4.0,
                solid_capstyle="round",
                zorder=20,
                path_effects=[pe.Stroke(linewidth=7.2, foreground="black", alpha=0.62), pe.Normal()],
            )
        ax.scatter(
            x,
            y,
            s=18,
            facecolor="#fff176",
            edgecolor="black",
            linewidth=0.55,
            zorder=21,
        )

    ax.text(
        88,
        2306,
        "Yellow track: TIMED/GUVI trajectory, time-matched to each 2-min SuperDARN panel",
        fontsize=18,
        color="black",
        bbox=dict(facecolor="white", edgecolor="0.45", alpha=0.86, boxstyle="round,pad=0.32"),
        zorder=30,
    )
    ax.text(
        88,
        2352,
        "Projection note: GUVI positions are converted with the same centered-dipole MLT/MLAT approximation used in the local screening plots.",
        fontsize=13,
        color="0.18",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.80, boxstyle="round,pad=0.22"),
        zorder=30,
    )

    out = ROOT / "superdarn_s_20150317_2230_2240_guvi_track_overlay.png"
    fig.savefig(out, dpi=180, bbox_inches="tight", pad_inches=0)
    plt.close(fig)

    m = total_mask
    lines = [
        "SuperDARN Canada southern convection map with time-matched TIMED/GUVI trajectory",
        "Base image: convection_maps_s_20150317_223800.png",
        "Base URL: https://sdc-serv.usask.ca/convection_plots/2015/03/convection_maps_s_20150317_223800.png",
        "Interval represented by the archive image: 2015-03-17 22:30-22:40 UT, five 2-min panels.",
        f"GUVI points overlaid per panel: {panel_counts}",
        (
            "GUVI overlaid total: "
            f"n={int(m.sum())}, UT={np.nanmin(guvi['ut'][m]):.3f}-{np.nanmax(guvi['ut'][m]):.3f}, "
            f"CD-MLAT={np.nanmin(guvi['mlat'][m]):.1f}..{np.nanmax(guvi['mlat'][m]):.1f}, "
            f"CD-MLT={np.nanmin(guvi['mlt'][m]):.1f}..{np.nanmax(guvi['mlt'][m]):.1f}, "
            f"O/N2 median={np.nanmedian(guvi['on2'][m]):.3f}, min={np.nanmin(guvi['on2'][m]):.3f}"
        ),
        "Visual SuperDARN note: dusk-side/subauroral channel is clear in the 22:30-22:40 UT southern panels; quick-look cross-polar potential is about 67-69 kV.",
    ]
    summary = ROOT / "superdarn_s_20150317_2230_2240_guvi_track_overlay_summary.txt"
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out)
    print(summary)


if __name__ == "__main__":
    main()

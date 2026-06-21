import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from make_dmsp_on2_overlay import (
    GUVI_16,
    GUVI_17,
    add_boxes,
    read_guvi_grid,
    sort_grid_by_lt,
)


ROOT = Path(__file__).resolve().parent


def read_dmsp_csv(path):
    rows = []
    with open(path, newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
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


def split_groups(indices, ut):
    groups = []
    if len(indices) == 0:
        return groups
    start = 0
    for pos in range(1, len(indices)):
        if indices[pos] - indices[pos - 1] > 5 or ut[indices[pos]] - ut[indices[pos - 1]] > 0.17:
            groups.append(indices[start:pos])
            start = pos
    groups.append(indices[start:])
    return groups


def select_near_9ut_passes(cols):
    selected = []
    for sat in sorted(set(cols["satellite"])):
        sat_mask = cols["satellite"] == sat
        target = (
            sat_mask
            & (cols["glat"] >= 40)
            & (cols["glat"] <= 70)
            & (cols["lt9"] >= 18)
            & (cols["lt9"] <= 24)
            & (cols["ut"] >= 7.0)
            & (cols["ut"] <= 10.0)
        )
        groups = split_groups(np.where(target)[0], cols["ut"])
        for group in groups:
            if len(group) < 80:
                continue
            selected.append(
                {
                    "sat": sat,
                    "box_idx": group,
                    "mid_ut": 0.5 * (cols["ut"][group].min() + cols["ut"][group].max()),
                    "t0": cols["ut"][group].min(),
                    "t1": cols["ut"][group].max(),
                }
            )
    return sorted(selected, key=lambda item: item["mid_ut"])


def plot_track_arrows():
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

    passes = select_near_9ut_passes(cols)
    print("Selected DMSP passes:")
    for item in passes:
        g = item["box_idx"]
        drift = cols["horizontal_ion_drift_mps"][g]
        print(
            "  {sat} UT {t0:.2f}-{t1:.2f}, n={n}, lat {lat0:.1f}-{lat1:.1f}, "
            "LT9 {lt0:.2f}-{lt1:.2f}, drift median={med:.0f}, min={mn:.0f}, max={mx:.0f}".format(
                sat=item["sat"],
                t0=item["t0"],
                t1=item["t1"],
                n=len(g),
                lat0=cols["glat"][g].min(),
                lat1=cols["glat"][g].max(),
                lt0=cols["lt9"][g].min(),
                lt1=cols["lt9"][g].max(),
                med=np.nanmedian(drift),
                mn=np.nanmin(drift),
                mx=np.nanmax(drift),
            )
        )

    fig, ax = plt.subplots(figsize=(10.8, 5.8), dpi=220)
    focus = (lt >= 17) & (lt <= 24)
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

    quiver_handle = None
    track_colors = {"F17": "#222222", "F18": "#555555"}
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
        order = np.argsort(cols["ut"][idx])
        idx = idx[order]
        if len(idx) == 0:
            continue

        ax.plot(
            cols["lt9"][idx],
            cols["glat"][idx],
            color=track_colors.get(sat, "#333333"),
            lw=1.7,
            alpha=0.9,
            zorder=4,
        )
        ax.scatter(
            cols["lt9"][idx],
            cols["glat"][idx],
            s=5,
            color=track_colors.get(sat, "#333333"),
            alpha=0.45,
            zorder=4,
        )

        arrow_idx = idx[::55]
        if len(arrow_idx) > 18:
            arrow_idx = arrow_idx[np.linspace(0, len(arrow_idx) - 1, 18, dtype=int)]
        drift = cols["horizontal_ion_drift_mps"][arrow_idx]
        # DMSP horizontal drift is the cross-track/zonal component for the polar orbit.
        # In the dusk sector, positive SAPS-like values are drawn westward, toward earlier LT.
        arrow_scale = 0.35
        u = -drift / 1000.0 * arrow_scale
        v = np.zeros_like(u)
        quiver_handle = ax.quiver(
            cols["lt9"][arrow_idx],
            cols["glat"][arrow_idx],
            u,
            v,
            drift,
            cmap="PiYG_r",
            clim=(-2500, 2500),
            angles="xy",
            scale_units="xy",
            scale=1,
            width=0.006,
            headwidth=4.8,
            headlength=6.0,
            headaxislength=5.2,
            pivot="mid",
            zorder=6,
        )

        mid = idx[len(idx) // 2]
        ax.text(
            cols["lt9"][mid] + 0.08,
            cols["glat"][mid],
            f"{sat} {item['t0']:.2f}-{item['t1']:.2f} UT",
            fontsize=8.5,
            color="black",
            ha="left",
            va="center",
            bbox=dict(fc="white", ec="0.45", alpha=0.82, boxstyle="round,pad=0.22"),
            zorder=7,
        )

    if quiver_handle is not None:
        cbar2 = fig.colorbar(quiver_handle, ax=ax, pad=0.075)
        cbar2.set_label("DMSP horizontal ion drift (m/s)")
        ax.quiverkey(
            quiver_handle,
            X=0.73,
            Y=0.07,
            U=0.35,
            label="1000 m/s",
            labelpos="E",
            coordinates="axes",
            fontproperties={"size": 8.5},
        )

    ax.set_xlim(17, 24)
    ax.set_ylim(35, 75)
    ax.set_xticks(np.arange(17, 25, 1))
    ax.set_xlabel("Geographic longitude converted to LT at 9 UT (hours)")
    ax.set_ylabel("Geographic latitude (deg)")
    ax.set_title("DMSP ion-drift tracks across the SAPS-related O/N2 depletion sector")
    ax.grid(alpha=0.22)
    ax.text(
        0.02,
        0.98,
        "Black curves: DMSP SSIES overpass tracks through the subauroral box near 9 UT.\n"
        "Arrows: observed horizontal/cross-track ion drift along each track; positive values are plotted westward.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.4,
        bbox=dict(fc="white", ec="0.45", alpha=0.84, boxstyle="round,pad=0.32"),
        zorder=8,
    )
    fig.tight_layout()
    out = ROOT / "guvi_on2_dmsp_track_arrows_lt9.png"
    fig.savefig(out)
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    plot_track_arrows()

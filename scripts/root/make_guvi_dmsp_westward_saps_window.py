import csv
from pathlib import Path

import matplotlib.pyplot as plt
import netCDF4
import numpy as np

from make_guvi_dmsp_mlt_candidate import GUVI_FILES, centered_dipole_coords, read_dmsp


ROOT = Path(__file__).resolve().parent


def read_guvi_raw_cd(path):
    with netCDF4.Dataset(path) as ds:
        doy = np.asarray(ds.variables["FRACTIONAL_DOY"][:], dtype=float)
        on2 = np.asarray(ds.variables["ON2"][:], dtype=float)
        glat = np.asarray(ds.variables["LATITUDE"][:], dtype=float)
        glon = np.asarray(ds.variables["LONGITUDE"][:], dtype=float)
        orbit = np.asarray(ds.variables["ORBIT"][:], dtype=float)
    valid = np.isfinite(on2) & (np.abs(on2) < 1e20) & np.isfinite(glat) & np.isfinite(glon)
    mlat, mlt = centered_dipole_coords(glat[valid], glon[valid], doy[valid])
    return {
        "ut": (doy[valid] % 1.0) * 24.0,
        "glat": glat[valid],
        "glon": ((glon[valid] + 180.0) % 360.0) - 180.0,
        "on2": on2[valid],
        "orbit": orbit[valid],
        "mlat": mlat,
        "mlt": mlt,
    }


def in_time_window(ut, center, width):
    half = width / 2.0
    start = center - half
    end = center + half
    if start < 0:
        return (ut >= start + 24.0) | (ut <= end)
    if end >= 24:
        return (ut >= start) | (ut <= end - 24.0)
    return (ut >= start) & (ut <= end)


def sector_mask(mlat, mlt, hemi, mlt_range):
    if hemi == "N":
        lat_mask = (mlat >= 48.0) & (mlat <= 70.0)
    else:
        lat_mask = (mlat >= -70.0) & (mlat <= -48.0)
    return lat_mask & (mlt >= mlt_range[0]) & (mlt <= mlt_range[1])


def find_candidate_window(guvi, dmsp, width=4.0):
    candidates = []
    for hemi in ["N", "S"]:
        for mlt_range in [(12.0, 18.0), (18.0, 24.0), (12.0, 24.0)]:
            guvi_sector = sector_mask(guvi["mlat"], guvi["mlt"], hemi, mlt_range)
            dmsp_sector = sector_mask(dmsp["cd_mlat"], dmsp["cd_mlt"], hemi, mlt_range)
            # Positive SSIES horizontal drift is treated as westward here.
            westward = dmsp["horizontal_ion_drift_mps"] > 0
            for center in np.arange(0.0, 24.0, 0.25):
                gm = guvi_sector & in_time_window(guvi["ut"], center, width)
                dm = dmsp_sector & in_time_window(dmsp["ut"], center, width) & westward
                if gm.sum() < 80 or dm.sum() < 80:
                    continue
                guvi_med = float(np.nanmedian(guvi["on2"][gm]))
                west = dmsp["horizontal_ion_drift_mps"][dm] / 1000.0
                p95 = float(np.nanpercentile(west, 95))
                wmax = float(np.nanmax(west))
                score = max(0.0, 1.0 - guvi_med) * (0.65 * p95 + 0.35 * wmax)
                candidates.append(
                    {
                        "score": score,
                        "center": center,
                        "width": width,
                        "hemi": hemi,
                        "mlt0": mlt_range[0],
                        "mlt1": mlt_range[1],
                        "guvi_count": int(gm.sum()),
                        "guvi_median": guvi_med,
                        "guvi_min": float(np.nanmin(guvi["on2"][gm])),
                        "dmsp_count": int(dm.sum()),
                        "west_median": float(np.nanmedian(west)),
                        "west_p95": p95,
                        "west_max": wmax,
                        "guvi_mask": gm,
                        "dmsp_mask": dm,
                    }
                )
    if not candidates:
        raise RuntimeError("No overlapping GUVI/DMSP westward candidate window found.")
    return sorted(candidates, key=lambda item: item["score"], reverse=True)


def split_track(lon, lat, max_jump=70.0):
    lon = np.asarray(lon, dtype=float)
    lat = np.asarray(lat, dtype=float)
    valid = np.isfinite(lon) & np.isfinite(lat)
    lon = lon[valid]
    lat = lat[valid]
    if len(lon) == 0:
        return []
    groups = []
    start = 0
    for i in range(1, len(lon)):
        if abs(lon[i] - lon[i - 1]) > max_jump:
            groups.append((lon[start:i], lat[start:i]))
            start = i
    groups.append((lon[start:], lat[start:]))
    return groups


def draw_westward_arrows(ax, lon, lat, west_kms, step=20, color="#7a1688"):
    order = np.argsort(lat)
    lon = lon[order]
    lat = lat[order]
    west_kms = west_kms[order]
    if len(lon) < 3:
        return
    positions = np.arange(0, len(lon), step)
    for pos in positions:
        speed = west_kms[pos]
        if not np.isfinite(speed) or speed <= 0:
            continue
        length_px = min(speed, 3.5) * 26.0
        start = ax.transData.transform((lon[pos], lat[pos]))
        end = start + np.array([-length_px, 0.0])
        end_xy = ax.transData.inverted().transform(end)
        ax.annotate(
            "",
            xy=end_xy,
            xytext=(lon[pos], lat[pos]),
            arrowprops=dict(
                arrowstyle="-|>",
                color=color,
                lw=0.70,
                mutation_scale=4.2,
                shrinkA=0,
                shrinkB=0,
            ),
            zorder=9,
        )


def add_dmsp_tracks_with_arrows(ax, dmsp, mask, arrow_step_divisor=28):
    for sat, color in [("F17", "#7a1688"), ("F18", "#5e3c99")]:
        m = mask & (dmsp["satellite"] == sat)
        if not np.any(m):
            continue
        idx = np.where(m)[0]
        idx = idx[np.argsort(dmsp["ut"][idx])]
        for lon, lat in split_track(dmsp["glon"][idx], dmsp["glat"][idx]):
            if len(lon) >= 2:
                ax.plot(lon, lat, color=color, lw=1.0, alpha=0.78, zorder=6, label=f"DMSP {sat}" if sat not in getattr(ax, "_sat_labeled", set()) else None)
                labeled = getattr(ax, "_sat_labeled", set())
                labeled.add(sat)
                ax._sat_labeled = labeled
        # Use all samples for arrows; the arrows point west and length scales with westward speed.
        draw_westward_arrows(
            ax,
            dmsp["glon"][idx],
            dmsp["glat"][idx],
            dmsp["horizontal_ion_drift_mps"][idx] / 1000.0,
            step=max(10, len(idx) // arrow_step_divisor),
            color=color,
        )


def write_summary(path, candidates):
    lines = [
        "Candidate GUVI/DMSP westward SAPS windows on 17 Mar 2015",
        "Positive DMSP SSIES horizontal ion drift is treated as westward.",
        "",
    ]
    for i, c in enumerate(candidates[:12], start=1):
        start = (c["center"] - c["width"] / 2.0) % 24.0
        end = (c["center"] + c["width"] / 2.0) % 24.0
        lines.append(
            f"{i:02d}. {c['hemi']} MLT {c['mlt0']:.0f}-{c['mlt1']:.0f}, "
            f"UT window {start:.2f}-{end:.2f} (center {c['center']:.2f}), "
            f"GUVI n={c['guvi_count']}, median O/N2={c['guvi_median']:.3f}, min={c['guvi_min']:.3f}; "
            f"DMSP westward n={c['dmsp_count']}, median={c['west_median']:.2f}, "
            f"p95={c['west_p95']:.2f}, max={c['west_max']:.2f} km/s; score={c['score']:.3f}"
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def plot_candidate(guvi, dmsp, candidate):
    start = (candidate["center"] - candidate["width"] / 2.0) % 24.0
    end = (candidate["center"] + candidate["width"] / 2.0) % 24.0
    gm = candidate["guvi_mask"]
    dm = candidate["dmsp_mask"]
    hemi = candidate["hemi"]

    if hemi == "N":
        ylim = (35.0, 80.0)
    else:
        ylim = (-80.0, -35.0)
    time_guvi = in_time_window(guvi["ut"], candidate["center"], candidate["width"])
    time_dmsp_west = in_time_window(dmsp["ut"], candidate["center"], candidate["width"]) & (
        dmsp["horizontal_ion_drift_mps"] > 0
    )
    region_guvi = gm & (guvi["glat"] >= ylim[0]) & (guvi["glat"] <= ylim[1])
    region_dmsp = dm & (dmsp["glat"] >= ylim[0]) & (dmsp["glat"] <= ylim[1])

    fig, axes = plt.subplots(
        3,
        1,
        figsize=(11.8, 11.2),
        dpi=220,
        gridspec_kw={"height_ratios": [1.25, 1.15, 0.9]},
    )
    fig.subplots_adjust(left=0.08, right=0.90, top=0.92, bottom=0.075, hspace=0.30)

    ax = axes[0]
    sc_global = ax.scatter(
        guvi["glon"][time_guvi],
        guvi["glat"][time_guvi],
        c=guvi["on2"][time_guvi],
        cmap="viridis",
        vmin=0,
        vmax=1.1,
        s=7,
        linewidths=0,
        alpha=0.78,
        label="GUVI O/N2",
        zorder=2,
    )
    add_dmsp_tracks_with_arrows(ax, dmsp, time_dmsp_west, arrow_step_divisor=44)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xticks(np.arange(-180, 181, 60))
    ax.set_yticks(np.arange(-80, 81, 40))
    ax.grid(alpha=0.23)
    ax.set_ylabel("Geographic latitude (deg)")
    ax.set_title(
        f"A. Global view in the common UT window {start:.2f}-{end:.2f}; DMSP arrows are westward only",
        loc="left",
        fontsize=10.6,
    )
    ax.legend(loc="lower left", ncol=3, fontsize=8.0, frameon=True)

    ax = axes[1]
    sc = ax.scatter(
        guvi["glon"][region_guvi],
        guvi["glat"][region_guvi],
        c=guvi["on2"][region_guvi],
        cmap="viridis",
        vmin=0,
        vmax=1.1,
        s=12,
        linewidths=0,
        alpha=0.88,
        label="GUVI O/N2",
        zorder=2,
    )
    add_dmsp_tracks_with_arrows(ax, dmsp, region_dmsp)
    ax.set_xlim(-180, 180)
    ax.set_ylim(*ylim)
    ax.set_xticks(np.arange(-180, 181, 60))
    ax.set_yticks(np.arange(np.ceil(ylim[0] / 10) * 10, ylim[1] + 1, 10))
    ax.grid(alpha=0.23)
    ax.set_ylabel("Geographic latitude (deg)")
    ax.set_title(
        f"B. Candidate sector: {hemi} MLT {candidate['mlt0']:.0f}-{candidate['mlt1']:.0f}, "
        f"UT {start:.2f}-{end:.2f}; arrows show westward DMSP drift",
        loc="left",
        fontsize=10.6,
    )
    cbar = fig.colorbar(sc_global, ax=axes[:2], pad=0.012, shrink=0.90)
    cbar.set_label("GUVI O/N2")

    ax2 = axes[2]
    for sat, color in [("F17", "#7a1688"), ("F18", "#5e3c99")]:
        m = region_dmsp & (dmsp["satellite"] == sat)
        if not np.any(m):
            continue
        idx = np.where(m)[0]
        idx = idx[np.argsort(dmsp["cd_mlat"][idx])]
        ax2.plot(
            dmsp["cd_mlat"][idx],
            dmsp["horizontal_ion_drift_mps"][idx] / 1000.0,
            ".-",
            ms=2.2,
            lw=0.75,
            color=color,
            alpha=0.70,
            label=sat,
        )
    ax2.axhline(0, color="k", lw=0.8)
    ax2.fill_between([-75, 75], [0, 0], [6, 6], color="#f1eef6", alpha=0.55, label="westward")
    ax2.set_xlim(ylim)
    ax2.set_ylim(-1.0, max(4.2, candidate["west_max"] + 0.6))
    ax2.grid(alpha=0.25)
    ax2.set_xlabel("Centered-dipole magnetic latitude (deg)")
    ax2.set_ylabel("DMSP horizontal drift (km/s)\npositive = westward")
    ax2.set_title(
        f"C. Westward component only: n={candidate['dmsp_count']}, "
        f"median={candidate['west_median']:.2f}, p95={candidate['west_p95']:.2f}, "
        f"max={candidate['west_max']:.2f} km/s",
        loc="left",
        fontsize=10.2,
    )
    ax2.legend(loc="upper right", fontsize=8.2, frameon=True)

    fig.suptitle(
        "GUVI O/N2 Observation and DMSP Westward SAPS-like Ion Drift in a Common Storm-day Window",
        fontsize=13.0,
    )
    fig.text(
        0.012,
        0.012,
        "Screening plot. GUVI and DMSP are selected in the same UT window and centered-dipole MLT sector. "
        "Only positive DMSP horizontal drift is used for the SAPS westward component; arrow length scales with westward speed.",
        fontsize=8.0,
        ha="left",
        va="bottom",
    )
    out = ROOT / "guvi_dmsp_westward_saps_candidate_window.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def main():
    guvi = read_guvi_raw_cd(GUVI_FILES["17 Mar"])
    dmsp = read_dmsp()
    candidates = find_candidate_window(guvi, dmsp, width=4.0)
    summary = ROOT / "guvi_dmsp_westward_saps_candidate_window_summary.txt"
    write_summary(summary, candidates)
    out = plot_candidate(guvi, dmsp, candidates[0])
    print(summary)
    print(out)
    print("Best candidate:")
    print(summary.read_text(encoding="utf-8").splitlines()[3])


if __name__ == "__main__":
    main()

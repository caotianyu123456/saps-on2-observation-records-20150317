import csv
from pathlib import Path

import matplotlib.pyplot as plt
import netCDF4
import numpy as np

from make_guvi_dmsp_mlt_candidate import (
    EX,
    EY,
    GUVI_FILES,
    M_AXIS,
    read_dmsp,
    subsolar_lat_lon,
    unit_vector,
)
from make_swarm_magnetosphere_mapping_screening import (
    read_rbsp_mapped,
    read_themis_mapped,
    unix_to_ut_hour,
)


ROOT = Path(__file__).resolve().parent


def read_guvi_grid(path):
    with netCDF4.Dataset(path) as ds:
        lon = np.asarray(ds.variables["GRID_LONGITUDE"][:], dtype=float)
        lat = np.asarray(ds.variables["GRID_LATITUDE"][:], dtype=float)
        grid = np.asarray(ds.variables["ON2_GRID_INTERPOLATED"][:], dtype=float)

    lon = ((lon + 180.0) % 360.0) - 180.0
    order = np.argsort(lon)
    lon = lon[order]
    grid = grid[:, order]
    grid[np.abs(grid) > 1e20] = np.nan
    return lon, lat, grid


def centered_dipole_to_geo(mlat, mlt, unix_time):
    mlat = np.asarray(mlat, dtype=float)
    mlt = np.asarray(mlt, dtype=float)
    unix_time = np.asarray(unix_time, dtype=float)
    doy = 76.0 + unix_to_ut_hour(unix_time) / 24.0
    ss_lat, ss_lon = subsolar_lat_lon(doy)
    rs = unit_vector(ss_lat, ss_lon)
    ss_phi = np.rad2deg(
        np.arctan2(np.einsum("i,ij->j", EY, rs), np.einsum("i,ij->j", EX, rs))
    )
    phi = np.deg2rad(ss_phi + (mlt - 12.0) * 15.0)
    mlat_rad = np.deg2rad(mlat)
    r = (
        EX[:, None] * (np.cos(mlat_rad) * np.cos(phi))[None, :]
        + EY[:, None] * (np.cos(mlat_rad) * np.sin(phi))[None, :]
        + M_AXIS[:, None] * np.sin(mlat_rad)[None, :]
    )
    glat = np.rad2deg(np.arcsin(np.clip(r[2], -1.0, 1.0)))
    glon = np.rad2deg(np.arctan2(r[1], r[0]))
    return glat, glon


def split_by_wrap(lon, lat, max_jump=60.0):
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


def add_track_lines(ax, lon, lat, color, lw=0.9, alpha=0.6, zorder=4, label=None):
    first = True
    for x, y in split_by_wrap(lon, lat):
        if len(x) < 2:
            continue
        ax.plot(
            x,
            y,
            color=color,
            lw=lw,
            alpha=alpha,
            zorder=zorder,
            label=label if first else None,
        )
        first = False


def add_common_axes_style(ax, ylim):
    ax.set_xlim(-180, 180)
    ax.set_ylim(*ylim)
    ax.set_xticks(np.arange(-180, 181, 60))
    ax.set_yticks(np.arange(np.ceil(ylim[0] / 20) * 20, ylim[1] + 1, 20))
    ax.grid(color="0.55", alpha=0.20, lw=0.5)
    ax.set_ylabel("Geographic latitude (deg)")


def collect_rbsp_arrays(records):
    out = {}
    for hemi in ["N", "S"]:
        selected = [rec for rec in records if rec["hemi"] == hemi]
        if not selected:
            continue
        out[hemi] = {
            "glat": np.concatenate([rec["glat"] for rec in selected]),
            "glon": np.concatenate([rec["glon"] for rec in selected]),
            "value": np.concatenate([rec["value"] for rec in selected]),
            "ut": np.concatenate([rec["ut"] for rec in selected]),
        }
    return out


def collect_themis_arrays(records):
    out = {}
    for hemi in ["N", "S"]:
        selected = [rec for rec in records if rec["hemi"] == hemi]
        if not selected:
            continue
        glat_all = []
        glon_all = []
        value_all = []
        ut_all = []
        for rec in selected:
            glat, glon = centered_dipole_to_geo(rec["mlat"], rec["mlt"], rec["time"])
            glat_all.append(glat)
            glon_all.append(glon)
            value_all.append(rec["value"])
            ut_all.append(rec["ut"])
        out[hemi] = {
            "glat": np.concatenate(glat_all),
            "glon": np.concatenate(glon_all),
            "value": np.concatenate(value_all),
            "ut": np.concatenate(ut_all),
        }
    return out


def write_summary(path, dmsp, rbsp, themis):
    lines = ["Global geographic overlay summary for 17 Mar 2015", ""]
    for sat in sorted(set(dmsp["satellite"])):
        m = (dmsp["satellite"] == sat) & (np.abs(dmsp["glat"]) >= 40) & (np.abs(dmsp["glat"]) <= 75)
        speed = np.abs(dmsp["horizontal_ion_drift_mps"][m]) / 1000.0
        lines.append(
            f"DMSP {sat}: n={int(m.sum())}, UT={np.nanmin(dmsp['ut'][m]):.2f}-{np.nanmax(dmsp['ut'][m]):.2f}, "
            f"|Vi| median={np.nanmedian(speed):.2f}, p95={np.nanpercentile(speed, 95):.2f}, max={np.nanmax(speed):.2f} km/s"
        )
    lines.append("")
    for hemi, data in rbsp.items():
        m = (np.abs(data["glat"]) >= 40) & (np.abs(data["glat"]) <= 75) & np.isfinite(data["value"])
        lines.append(
            f"RBSP {hemi} footpoints: n={int(m.sum())}, UT={np.nanmin(data['ut'][m]):.2f}-{np.nanmax(data['ut'][m]):.2f}, "
            f"|E| median={np.nanmedian(data['value'][m]):.2f}, p95={np.nanpercentile(data['value'][m], 95):.2f}, max={np.nanmax(data['value'][m]):.2f} mV/m"
        )
    lines.append("")
    for hemi, data in themis.items():
        m = (np.abs(data["glat"]) >= 40) & (np.abs(data["glat"]) <= 75) & np.isfinite(data["value"])
        lines.append(
            f"THEMIS {hemi} approximate footpoints: n={int(m.sum())}, UT={np.nanmin(data['ut'][m]):.2f}-{np.nanmax(data['ut'][m]):.2f}, "
            f"|Vi| median={np.nanmedian(data['value'][m]):.2f}, p95={np.nanpercentile(data['value'][m], 95):.2f}, max={np.nanmax(data['value'][m]):.2f} km/s"
        )
    lines.append("")
    lines.append(
        "Caveat: GUVI is a daily gridded dayside O/N2 product. RBSP uses MagEphem geographic footpoints. "
        "THEMIS footpoints are approximate centered-dipole inverse mapping from GSM-derived MLT/footpoint latitude."
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    lon, lat, grid16 = read_guvi_grid(GUVI_FILES["16 Mar"])
    _, _, grid17 = read_guvi_grid(GUVI_FILES["17 Mar"])
    delta = grid17 - grid16
    dmsp = read_dmsp()
    rbsp = collect_rbsp_arrays(read_rbsp_mapped())
    themis = collect_themis_arrays(read_themis_mapped())

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(12.4, 9.0),
        dpi=220,
        gridspec_kw={"height_ratios": [1.35, 1.0]},
    )
    fig.subplots_adjust(left=0.07, right=0.87, top=0.91, bottom=0.085, hspace=0.18)

    mesh = None
    for ax, ylim, title in [
        (axes[0], (-90, 90), "A. Global geographic map"),
        (axes[1], (-80, -35), "B. Southern subauroral zoom"),
    ]:
        mesh = ax.pcolormesh(
            lon,
            lat,
            delta,
            cmap="RdBu_r",
            vmin=-0.8,
            vmax=0.8,
            shading="auto",
            alpha=0.86,
            zorder=1,
        )

        high_drift_plotted = False
        for sat, color in [("F17", "#b2182b"), ("F18", "#542788")]:
            m = (
                (dmsp["satellite"] == sat)
                & (np.abs(dmsp["glat"]) >= 40)
                & (np.abs(dmsp["glat"]) <= 75)
            )
            order = np.argsort(dmsp["ut"][m])
            lon_sat = dmsp["glon"][m][order]
            lat_sat = dmsp["glat"][m][order]
            add_track_lines(ax, lon_sat, lat_sat, color=color, lw=0.62, alpha=0.38, zorder=4, label=f"DMSP {sat}")
            speed = np.abs(dmsp["horizontal_ion_drift_mps"][m][order]) / 1000.0
            fast = speed >= 1.5
            ax.scatter(
                lon_sat[fast],
                lat_sat[fast],
                s=5.2,
                color="#d7301f",
                alpha=0.72,
                linewidths=0,
                zorder=7,
                label="DMSP |Vi| > 1.5 km/s" if not high_drift_plotted else None,
            )
            high_drift_plotted = high_drift_plotted or bool(np.any(fast))

        for hemi, data in rbsp.items():
            m = (np.abs(data["glat"]) >= 40) & (np.abs(data["glat"]) <= 75)
            order = np.argsort(data["ut"][m])
            x = data["glon"][m][order]
            y = data["glat"][m][order]
            value = data["value"][m][order]
            add_track_lines(
                ax,
                x,
                y,
                color="#ffb000",
                lw=0.62,
                alpha=0.40,
                zorder=5,
                label=f"RBSP {hemi} footpoint",
            )
            thin = np.arange(0, len(x), 8)
            ax.scatter(
                x[thin],
                y[thin],
                s=3.0 + np.clip(value[thin], 0, 16) * 0.75,
                facecolors="#ffb000",
                edgecolors="black",
                linewidths=0.10,
                alpha=0.50,
                zorder=6,
            )

        for hemi, data in themis.items():
            m = (np.abs(data["glat"]) >= 40) & (np.abs(data["glat"]) <= 75)
            order = np.argsort(data["ut"][m])
            x = data["glon"][m][order]
            y = data["glat"][m][order]
            value = data["value"][m][order]
            add_track_lines(
                ax,
                x,
                y,
                color="#1b9e77",
                lw=0.70,
                alpha=0.36,
                zorder=8,
                label=f"THEMIS {hemi} approx. footpoint",
            )
            thin = np.arange(0, len(x), 6)
            ax.scatter(
                x[thin],
                y[thin],
                s=3.0 + np.clip(value[thin], 0, 500) * 0.018,
                marker="^",
                facecolors="#1b9e77",
                edgecolors="black",
                linewidths=0.08,
                alpha=0.42,
                zorder=9,
            )

        add_common_axes_style(ax, ylim)
        ax.set_title(title, loc="left", fontsize=11.2)

    axes[1].set_xlabel("Geographic longitude (deg)")
    handles, labels = axes[0].get_legend_handles_labels()
    unique = {}
    for handle, label in zip(handles, labels):
        unique.setdefault(label, handle)
    axes[0].legend(
        unique.values(),
        unique.keys(),
        loc="lower left",
        ncol=3,
        fontsize=7.2,
        frameon=True,
    )
    cax = fig.add_axes([0.895, 0.18, 0.025, 0.64])
    cbar = fig.colorbar(mesh, cax=cax)
    cbar.set_label("GUVI O/N2 anomaly (17 Mar minus 16 Mar)")
    fig.suptitle(
        "17 Mar 2015 Geographic Overlay: GUVI O/N2 Depletion with DMSP, RBSP, and THEMIS Tracks",
        fontsize=13.3,
    )
    fig.text(
        0.012,
        0.006,
        "DMSP red points mark |Vi| > 1.5 km/s. RBSP marker size scales with mapped |E|. "
        "THEMIS marker size scales with magnetospheric ion bulk speed after approximate centered-dipole footpoint mapping.",
        fontsize=8.0,
        ha="left",
        va="bottom",
    )

    out = ROOT / "global_guvi_dmsp_rbsp_themis_tracks_overlay.png"
    fig.savefig(out)
    plt.close(fig)
    summary = ROOT / "global_guvi_dmsp_rbsp_themis_tracks_overlay_summary.txt"
    write_summary(summary, dmsp, rbsp, themis)
    print(out)
    print(summary)


if __name__ == "__main__":
    main()

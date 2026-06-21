import csv
from pathlib import Path

import cdflib
import matplotlib.pyplot as plt
import netCDF4
import numpy as np

from make_guvi_dmsp_mlt_candidate import EX, EY, GUVI_FILES, M_AXIS, read_dmsp, subsolar_lat_lon, unit_vector
from make_swarm_magnetosphere_mapping_screening import read_themis_mapped, unix_to_ut_hour


ROOT = Path(__file__).resolve().parent
SWARM_CACHE = {
    "A": ROOT / "swarm_A_MAG_LR_20150317_track.csv",
    "B": ROOT / "swarm_B_MAG_LR_20150317_track.csv",
    "C": ROOT / "swarm_C_MAG_LR_20150317_track.csv",
}


def read_guvi_raw(path):
    with netCDF4.Dataset(path) as ds:
        lat = np.asarray(ds.variables["LATITUDE"][:], dtype=float)
        lon = np.asarray(ds.variables["LONGITUDE"][:], dtype=float)
        on2 = np.asarray(ds.variables["ON2"][:], dtype=float)
        doy = np.asarray(ds.variables["FRACTIONAL_DOY"][:], dtype=float)
        orbit = np.asarray(ds.variables["ORBIT"][:], dtype=float)
    ut = (doy % 1.0) * 24.0
    valid = np.isfinite(lat) & np.isfinite(lon) & np.isfinite(on2) & (np.abs(on2) < 1e20)
    lon = ((lon + 180.0) % 360.0) - 180.0
    return {
        "lat": lat[valid],
        "lon": lon[valid],
        "on2": on2[valid],
        "ut": ut[valid],
        "orbit": orbit[valid],
    }


def fetch_swarm_track(probe):
    path = SWARM_CACHE[probe]
    if path.exists():
        rows = []
        with open(path, newline="") as handle:
            for row in csv.DictReader(handle):
                rows.append({key: float(value) for key, value in row.items()})
        return {key: np.asarray([row[key] for row in rows], dtype=float) for key in rows[0]}

    from hapiclient import hapi

    server = "https://vires.services/hapi"
    dataset = f"SW_OPER_MAG{probe}_LR_1B"
    data, _ = hapi(
        server,
        dataset,
        "Latitude,Longitude,Radius",
        "2015-03-17T00:00:00Z",
        "2015-03-18T00:00:00Z",
    )
    lat = np.asarray(data["Latitude"], dtype=float)
    lon = ((np.asarray(data["Longitude"], dtype=float) + 180.0) % 360.0) - 180.0
    radius = np.asarray(data["Radius"], dtype=float)
    # HAPI MAG LR is 1-s cadence. This script stores only every 20 s for plotting.
    keep = np.arange(0, len(lat), 20)
    seconds = keep.astype(float)
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["seconds", "lat", "lon", "radius"])
        writer.writeheader()
        for i in keep:
            writer.writerow({"seconds": float(i), "lat": lat[i], "lon": lon[i], "radius": radius[i]})
    return {"seconds": seconds, "lat": lat[keep], "lon": lon[keep], "radius": radius[keep]}


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


def collect_themis_geo_tracks():
    tracks = []
    for rec in read_themis_mapped():
        glat, glon = centered_dipole_to_geo(rec["mlat"], rec["mlt"], rec["time"])
        tracks.append(
            {
                "source": rec["source"],
                "hemi": rec["hemi"],
                "glat": glat,
                "glon": glon,
                "ut": rec["ut"],
                "speed": rec["value"],
            }
        )
    return tracks


def split_by_wrap(lon, lat, *extra, max_jump=60.0):
    lon = np.asarray(lon, dtype=float)
    lat = np.asarray(lat, dtype=float)
    valid = np.isfinite(lon) & np.isfinite(lat)
    for arr in extra:
        valid &= np.isfinite(arr)
    lon = lon[valid]
    lat = lat[valid]
    extras = [np.asarray(arr, dtype=float)[valid] for arr in extra]
    if len(lon) == 0:
        return []
    groups = []
    start = 0
    for i in range(1, len(lon)):
        if abs(lon[i] - lon[i - 1]) > max_jump:
            groups.append((lon[start:i], lat[start:i], *[arr[start:i] for arr in extras]))
            start = i
    groups.append((lon[start:], lat[start:], *[arr[start:] for arr in extras]))
    return groups


def plot_lines(ax, lon, lat, color, label=None, lw=0.75, alpha=0.55, zorder=4):
    first = True
    for x, y in split_by_wrap(lon, lat):
        if len(x) < 2:
            continue
        ax.plot(x, y, color=color, lw=lw, alpha=alpha, label=label if first else None, zorder=zorder)
        first = False


def add_axes_style(ax, ylim):
    ax.set_xlim(-180, 180)
    ax.set_ylim(*ylim)
    ax.set_xticks(np.arange(-180, 181, 60))
    ax.set_yticks(np.arange(np.ceil(ylim[0] / 20) * 20, ylim[1] + 1, 20))
    ax.grid(color="0.5", alpha=0.22, lw=0.5)
    ax.set_ylabel("Geographic latitude (deg)")


def add_guvi_points(ax, guvi, ylim):
    region = (guvi["lat"] >= ylim[0]) & (guvi["lat"] <= ylim[1])
    return ax.scatter(
        guvi["lon"][region],
        guvi["lat"][region],
        c=guvi["on2"][region],
        s=5.0 if ylim[0] < -85 else 8.0,
        cmap="viridis",
        vmin=0,
        vmax=1.1,
        linewidths=0,
        alpha=0.82,
        zorder=2,
        label="GUVI O/N2",
    )


def add_dmsp(ax, dmsp, ylim):
    for sat, color in [("F17", "#7a1688"), ("F18", "#5e3c99")]:
        m = (
            (dmsp["satellite"] == sat)
            & (dmsp["glat"] >= ylim[0])
            & (dmsp["glat"] <= ylim[1])
            & (np.abs(dmsp["glat"]) <= 82)
        )
        order = np.argsort(dmsp["ut"][m])
        lon = dmsp["glon"][m][order]
        lat = dmsp["glat"][m][order]
        speed = np.abs(dmsp["horizontal_ion_drift_mps"][m][order]) / 1000.0
        plot_lines(ax, lon, lat, color=color, label=f"DMSP {sat}", lw=0.65, alpha=0.42, zorder=4)
        fast = speed >= 1.5
        ax.scatter(
            lon[fast],
            lat[fast],
            s=5.5,
            color="#d7301f",
            alpha=0.76,
            linewidths=0,
            zorder=6,
            label="DMSP |Vi| > 1.5 km/s" if sat == "F17" else None,
        )


def add_swarm(ax, tracks, ylim):
    colors = {"A": "#222222", "B": "#666666", "C": "#999999"}
    for probe, track in tracks.items():
        m = (track["lat"] >= ylim[0]) & (track["lat"] <= ylim[1])
        plot_lines(
            ax,
            track["lon"][m],
            track["lat"][m],
            color=colors[probe],
            label=f"Swarm {probe} MAG orbit",
            lw=0.72,
            alpha=0.52,
            zorder=5,
        )


def add_themis(ax, tracks, ylim):
    last_scatter = None
    for rec in tracks:
        m = (
            (rec["glat"] >= ylim[0])
            & (rec["glat"] <= ylim[1])
            & (np.abs(rec["glat"]) >= 40)
            & np.isfinite(rec["speed"])
        )
        if not np.any(m):
            continue
        order = np.argsort(rec["ut"][m])
        lon = rec["glon"][m][order]
        lat = rec["glat"][m][order]
        speed = rec["speed"][m][order]
        label = "THEMIS mapped ion speed" if rec["source"] == "THA" and rec["hemi"] == "N" else None
        plot_lines(ax, lon, lat, color="#1b9e77", label=label, lw=0.78, alpha=0.34, zorder=7)
        thin = np.arange(0, len(lon), 5)
        last_scatter = ax.scatter(
            lon[thin],
            lat[thin],
            c=np.clip(speed[thin], 0, 600),
            cmap="plasma",
            vmin=0,
            vmax=600,
            s=7.0,
            marker="^",
            alpha=0.62,
            linewidths=0,
            zorder=8,
        )
    return last_scatter


def write_summary(path, guvi, swarm_tracks, dmsp, themis_tracks):
    lines = ["Global raw-track overlay summary for 17 Mar 2015", ""]
    lines.append(
        f"GUVI raw valid O/N2 points: n={len(guvi['on2'])}, "
        f"UT={np.nanmin(guvi['ut']):.2f}-{np.nanmax(guvi['ut']):.2f}, "
        f"O/N2 median={np.nanmedian(guvi['on2']):.3f}, min={np.nanmin(guvi['on2']):.3f}, max={np.nanmax(guvi['on2']):.3f}"
    )
    for probe, track in swarm_tracks.items():
        lines.append(
            f"Swarm {probe} MAG orbit points plotted: n={len(track['lat'])}, "
            f"lat={np.nanmin(track['lat']):.1f} to {np.nanmax(track['lat']):.1f}, "
            f"lon={np.nanmin(track['lon']):.1f} to {np.nanmax(track['lon']):.1f}"
        )
    for sat in sorted(set(dmsp["satellite"])):
        m = dmsp["satellite"] == sat
        speed = np.abs(dmsp["horizontal_ion_drift_mps"][m]) / 1000.0
        lines.append(
            f"DMSP {sat}: n={int(m.sum())}, |Vi| median={np.nanmedian(speed):.2f}, "
            f"p95={np.nanpercentile(speed, 95):.2f}, max={np.nanmax(speed):.2f} km/s"
        )
    speed_all = np.concatenate([rec["speed"][np.isfinite(rec["speed"])] for rec in themis_tracks])
    lines.append(
        f"THEMIS mapped ion speed points: n={len(speed_all)}, median={np.nanmedian(speed_all):.2f}, "
        f"p95={np.nanpercentile(speed_all, 95):.2f}, max={np.nanmax(speed_all):.2f} km/s"
    )
    lines.append("")
    lines.append(
        "Caveats: GUVI is raw dayside O/N2 along TIMED/GUVI swaths. Swarm MAG gives orbit only here, not ion drift. "
        "THEMIS mapped tracks use approximate centered-dipole inverse mapping from GSM-derived footpoint latitude/MLT."
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    guvi = read_guvi_raw(GUVI_FILES["17 Mar"])
    dmsp = read_dmsp()
    swarm_tracks = {}
    for probe in ["A", "B", "C"]:
        try:
            swarm_tracks[probe] = fetch_swarm_track(probe)
        except Exception as exc:
            print(f"Swarm {probe} unavailable: {exc}")
    themis_tracks = collect_themis_geo_tracks()

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(12.8, 9.2),
        dpi=220,
        gridspec_kw={"height_ratios": [1.35, 1.0]},
    )
    fig.subplots_adjust(left=0.07, right=0.86, top=0.91, bottom=0.09, hspace=0.18)

    guvi_scatter = None
    themis_scatter = None
    for ax, ylim, title in [
        (axes[0], (-90, 90), "A. Global geographic map"),
        (axes[1], (-80, -35), "B. Southern subauroral zoom"),
    ]:
        guvi_scatter = add_guvi_points(ax, guvi, ylim)
        add_swarm(ax, swarm_tracks, ylim)
        add_dmsp(ax, dmsp, ylim)
        themis_scatter = add_themis(ax, themis_tracks, ylim) or themis_scatter
        add_axes_style(ax, ylim)
        ax.set_title(title, loc="left", fontsize=11.2)

    axes[1].set_xlabel("Geographic longitude (deg)")
    handles, labels = axes[0].get_legend_handles_labels()
    unique = {}
    for handle, label in zip(handles, labels):
        if label and label not in unique:
            unique[label] = handle
    axes[0].legend(unique.values(), unique.keys(), loc="lower left", ncol=3, fontsize=7.1, frameon=True)

    cax1 = fig.add_axes([0.885, 0.53, 0.023, 0.32])
    cbar1 = fig.colorbar(guvi_scatter, cax=cax1)
    cbar1.set_label("GUVI O/N2")
    if themis_scatter is not None:
        cax2 = fig.add_axes([0.885, 0.15, 0.023, 0.27])
        cbar2 = fig.colorbar(themis_scatter, cax=cax2)
        cbar2.set_label("THEMIS mapped |Vi| (km/s)")

    fig.suptitle(
        "17 Mar 2015 Global Raw-Track Overlay: GUVI O/N2 with Swarm, DMSP, and Mapped THEMIS",
        fontsize=13.3,
    )
    fig.text(
        0.012,
        0.010,
        "GUVI raw swath points are colored by O/N2. DMSP red points mark |Vi| > 1.5 km/s. "
        "Swarm MAG tracks show orbit only. THEMIS ion bulk speed is mapped approximately to ionospheric footpoints.",
        fontsize=8.0,
        ha="left",
        va="bottom",
    )

    out = ROOT / "global_guvi_raw_tracks_swarm_dmsp_themis_overlay.png"
    fig.savefig(out)
    plt.close(fig)
    summary = ROOT / "global_guvi_raw_tracks_swarm_dmsp_themis_overlay_summary.txt"
    write_summary(summary, guvi, swarm_tracks, dmsp, themis_tracks)
    print(out)
    print(summary)


if __name__ == "__main__":
    main()

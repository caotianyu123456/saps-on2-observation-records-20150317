from pathlib import Path

import cdflib  # noqa: F401 - imported so dependency failures happen early.
import matplotlib.pyplot as plt
import netCDF4
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from make_guvi_dmsp_mlt_candidate import (
    EX,
    EY,
    GUVI_FILES,
    M_AXIS,
    centered_dipole_coords,
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
SUBAURORAL_ABS_MLAT = (48.0, 70.0)
FAST_DMSP_KMS = 1.5


def read_guvi_observed_grid(path):
    with netCDF4.Dataset(path) as ds:
        lon = np.asarray(ds.variables["GRID_LONGITUDE"][:], dtype=float)
        lat = np.asarray(ds.variables["GRID_LATITUDE"][:], dtype=float)
        grid = np.asarray(ds.variables["ON2_GRID_INTERPOLATED"][:], dtype=float)

    lon = ((lon + 180.0) % 360.0) - 180.0
    lon_order = np.argsort(lon)
    lat_order = np.argsort(lat)
    lon = lon[lon_order]
    lat = lat[lat_order]
    grid = grid[lat_order, :][:, lon_order]
    grid[np.abs(grid) > 1e20] = np.nan
    return lon, lat, grid


def read_guvi_raw_points(path):
    with netCDF4.Dataset(path) as ds:
        doy = np.asarray(ds.variables["FRACTIONAL_DOY"][:], dtype=float)
        on2 = np.asarray(ds.variables["ON2"][:], dtype=float)
        lat = np.asarray(ds.variables["LATITUDE"][:], dtype=float)
        lon = np.asarray(ds.variables["LONGITUDE"][:], dtype=float)
    valid = np.isfinite(on2) & (np.abs(on2) < 1e20) & np.isfinite(lat) & np.isfinite(lon)
    lon = ((lon[valid] + 180.0) % 360.0) - 180.0
    mlat, mlt = centered_dipole_coords(lat[valid], lon, doy[valid])
    return {
        "ut": (doy[valid] % 1.0) * 24.0,
        "glat": lat[valid],
        "glon": lon,
        "mlat": mlat,
        "mlt": mlt,
        "on2": on2[valid],
    }


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


def split_by_dateline(lon, lat, *extra, max_jump=70.0):
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


def split_track_segments(lon, lat, ut=None, max_lon_jump=70.0, max_lat_jump=12.0, max_time_gap=0.08):
    lon = np.asarray(lon, dtype=float)
    lat = np.asarray(lat, dtype=float)
    valid = np.isfinite(lon) & np.isfinite(lat)
    if ut is not None:
        ut = np.asarray(ut, dtype=float)
        valid &= np.isfinite(ut)
    lon = lon[valid]
    lat = lat[valid]
    ut = ut[valid] if ut is not None else None
    if len(lon) == 0:
        return []

    groups = []
    start = 0
    for i in range(1, len(lon)):
        split = abs(lon[i] - lon[i - 1]) > max_lon_jump
        split |= abs(lat[i] - lat[i - 1]) > max_lat_jump
        if ut is not None:
            split |= (ut[i] - ut[i - 1]) > max_time_gap
        if split:
            groups.append((lon[start:i], lat[start:i]))
            start = i
    groups.append((lon[start:], lat[start:]))
    return groups


def magnetic_latitude_mesh():
    lon = np.linspace(-180.0, 180.0, 721)
    lat = np.linspace(-90.0, 90.0, 361)
    lon2, lat2 = np.meshgrid(lon, lat)
    doy = np.full(lon2.size, 76.5)
    mlat, _ = centered_dipole_coords(lat2.ravel(), lon2.ravel(), doy)
    return lon2, lat2, mlat.reshape(lon2.shape)


def add_subauroral_bands(ax, lon2, lat2, mlat2):
    lower, upper = SUBAURORAL_ABS_MLAT
    north = np.where((mlat2 >= lower) & (mlat2 <= upper), 1.0, np.nan)
    south = np.where((mlat2 <= -lower) & (mlat2 >= -upper), 1.0, np.nan)
    ax.contourf(lon2, lat2, north, levels=[0.5, 1.5], colors=["#f2b84b"], alpha=0.14, zorder=3)
    ax.contourf(lon2, lat2, south, levels=[0.5, 1.5], colors=["#41b6c4"], alpha=0.14, zorder=3)
    ax.contour(lon2, lat2, mlat2, levels=[lower, upper], colors=["#b66a00"], linewidths=0.70, zorder=4)
    ax.contour(lon2, lat2, mlat2, levels=[-upper, -lower], colors=["#087d8f"], linewidths=0.70, zorder=4)
    ax.text(
        -176,
        61,
        "N subauroral\n+48 to +70 CD MLAT",
        fontsize=7.7,
        color="#7a4700",
        va="center",
        bbox=dict(fc="white", ec="none", alpha=0.70, pad=1.4),
        zorder=10,
    )
    ax.text(
        -176,
        -61,
        "S subauroral\n-70 to -48 CD MLAT",
        fontsize=7.7,
        color="#075c69",
        va="center",
        bbox=dict(fc="white", ec="none", alpha=0.70, pad=1.4),
        zorder=10,
    )


def style_global_axes(ax):
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xticks(np.arange(-180, 181, 60))
    ax.set_yticks(np.arange(-80, 81, 40))
    ax.grid(color="0.35", alpha=0.20, lw=0.55)
    ax.set_xlabel("Geographic longitude (deg)")
    ax.set_ylabel("Geographic latitude (deg)")


def add_guvi_base(ax, lon, lat, on2_grid):
    mesh = ax.pcolormesh(
        lon,
        lat,
        on2_grid,
        cmap="viridis",
        vmin=0.0,
        vmax=1.1,
        shading="auto",
        alpha=0.86,
        zorder=1,
    )
    return mesh


def add_dmsp_drift(ax, dmsp):
    lower, upper = SUBAURORAL_ABS_MLAT
    sat_colors = {"F17": "#7a1688", "F18": "#4d4d9b"}
    fast_handles = []
    for sat, color in sat_colors.items():
        m = (
            (dmsp["satellite"] == sat)
            & (np.abs(dmsp["cd_mlat"]) >= lower)
            & (np.abs(dmsp["cd_mlat"]) <= upper)
            & (np.abs(dmsp["glat"]) <= 86.0)
        )
        idx = np.where(m)[0]
        if len(idx) == 0:
            continue
        idx = idx[np.argsort(dmsp["ut"][idx])]
        for x, y in split_track_segments(dmsp["glon"][idx], dmsp["glat"][idx], dmsp["ut"][idx]):
            if len(x) >= 2:
                ax.plot(x, y, color=color, lw=0.58, alpha=0.42, zorder=6)
        speed = np.abs(dmsp["horizontal_ion_drift_mps"][idx]) / 1000.0
        fast = speed >= FAST_DMSP_KMS
        if np.any(fast):
            handle = ax.scatter(
                dmsp["glon"][idx][fast],
                dmsp["glat"][idx][fast],
                s=5.0 + np.clip(speed[fast], 0, 4.0) * 1.4,
                color="#d7301f",
                alpha=0.70,
                linewidths=0,
                zorder=8,
            )
            fast_handles.append(handle)
    return fast_handles[-1] if fast_handles else None


def add_rbsp_efield(ax, rbsp_records):
    lower, upper = SUBAURORAL_ABS_MLAT
    for rec in rbsp_records:
        m = (
            (np.abs(rec["mlat"]) >= lower)
            & (np.abs(rec["mlat"]) <= upper)
            & np.isfinite(rec["value"])
            & np.isfinite(rec["glat"])
            & np.isfinite(rec["glon"])
        )
        if not np.any(m):
            continue
        order = np.argsort(rec["ut"][m])
        lon = ((rec["glon"][m][order] + 180.0) % 360.0) - 180.0
        lat = rec["glat"][m][order]
        value = rec["value"][m][order]
        ut = rec["ut"][m][order]
        for x, y in split_track_segments(lon, lat, ut, max_time_gap=0.14):
            if len(x) >= 2:
                ax.plot(x, y, color="#ffb000", lw=0.58, alpha=0.40, zorder=7)
        thin = np.arange(0, len(lon), 10)
        ax.scatter(
            lon[thin],
            lat[thin],
            s=7.0 + np.clip(value[thin], 0, 18.0) * 1.35,
            marker="o",
            facecolors="#ffb000",
            edgecolors="black",
            linewidths=0.12,
            alpha=0.56,
            zorder=9,
        )


def add_themis_ion_speed(ax, themis_records):
    lower, upper = SUBAURORAL_ABS_MLAT
    for rec in themis_records:
        m = (
            (np.abs(rec["mlat"]) >= lower)
            & (np.abs(rec["mlat"]) <= upper)
            & np.isfinite(rec["value"])
            & np.isfinite(rec["mlt"])
            & np.isfinite(rec["time"])
        )
        if not np.any(m):
            continue
        glat, glon = centered_dipole_to_geo(rec["mlat"][m], rec["mlt"][m], rec["time"][m])
        glon = ((glon + 180.0) % 360.0) - 180.0
        order = np.argsort(rec["ut"][m])
        glon = glon[order]
        glat = glat[order]
        speed = rec["value"][m][order]
        ut = rec["ut"][m][order]
        for x, y in split_track_segments(glon, glat, ut, max_time_gap=0.14):
            if len(x) >= 2:
                ax.plot(x, y, color="#1b9e77", lw=0.58, alpha=0.34, zorder=10)
        thin = np.arange(0, len(glon), 8)
        ax.scatter(
            glon[thin],
            glat[thin],
            s=7.0 + np.clip(speed[thin], 0, 650.0) * 0.030,
            marker="^",
            facecolors="#1b9e77",
            edgecolors="black",
            linewidths=0.10,
            alpha=0.60,
            zorder=11,
        )


def add_base_legend(ax):
    handles = [
        Patch(facecolor="#f2b84b", edgecolor="#b66a00", alpha=0.26, label="N subauroral band"),
        Patch(facecolor="#41b6c4", edgecolor="#087d8f", alpha=0.26, label="S subauroral band"),
    ]
    ax.legend(handles=handles, loc="lower left", ncol=2, fontsize=7.8, frameon=True)


def add_overlay_legend(ax):
    handles = [
        Patch(facecolor="#f2b84b", edgecolor="#b66a00", alpha=0.26, label="N subauroral band"),
        Patch(facecolor="#41b6c4", edgecolor="#087d8f", alpha=0.26, label="S subauroral band"),
        Line2D([0], [0], color="#7a1688", lw=1.2, label="DMSP SSIES track"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#d7301f", markersize=4.8, label="DMSP |Vi| >= 1.5 km/s"),
        Line2D([0], [0], marker="^", color="none", markerfacecolor="#1b9e77", markeredgecolor="black", markersize=5.8, label="THEMIS mapped ion |V|"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#ffb000", markeredgecolor="black", markersize=5.8, label="RBSP mapped |E|"),
    ]
    ax.legend(handles=handles, loc="lower left", ncol=3, fontsize=7.1, frameon=True)


def plot_base_map(lon, lat, grid, lon2, lat2, mlat2):
    fig, ax = plt.subplots(figsize=(12.6, 6.7), dpi=240)
    fig.subplots_adjust(left=0.065, right=0.88, top=0.90, bottom=0.12)
    mesh = add_guvi_base(ax, lon, lat, grid)
    add_subauroral_bands(ax, lon2, lat2, mlat2)
    style_global_axes(ax)
    add_base_legend(ax)
    cax = fig.add_axes([0.90, 0.19, 0.025, 0.62])
    cbar = fig.colorbar(mesh, cax=cax)
    cbar.set_label("GUVI O/N2")
    ax.set_title("17 Mar 2015 TIMED/GUVI observed O/N2 with northern and southern subauroral bands", fontsize=12.3)
    fig.text(
        0.012,
        0.020,
        "Subauroral bands are centered-dipole magnetic latitude 48-70 deg in each hemisphere, drawn on geographic coordinates.",
        fontsize=8.0,
        ha="left",
        va="bottom",
    )
    out = ROOT / "guvi_on2_20150317_global_subauroral_bands.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def plot_overlay_map(lon, lat, grid, lon2, lat2, mlat2, dmsp, rbsp_records, themis_records):
    fig, ax = plt.subplots(figsize=(12.9, 6.9), dpi=240)
    fig.subplots_adjust(left=0.065, right=0.88, top=0.90, bottom=0.12)
    mesh = add_guvi_base(ax, lon, lat, grid)
    add_subauroral_bands(ax, lon2, lat2, mlat2)
    add_dmsp_drift(ax, dmsp)
    add_rbsp_efield(ax, rbsp_records)
    add_themis_ion_speed(ax, themis_records)
    style_global_axes(ax)
    add_overlay_legend(ax)
    cax = fig.add_axes([0.90, 0.19, 0.025, 0.62])
    cbar = fig.colorbar(mesh, cax=cax)
    cbar.set_label("GUVI O/N2")
    ax.set_title("17 Mar 2015 GUVI O/N2 with subauroral bands and drift-related measurements", fontsize=12.3)
    fig.text(
        0.012,
        0.018,
        "DMSP gives low-altitude horizontal ion drift. THEMIS ion bulk speed is mapped approximately to conjugate footpoints. "
        "RBSP EFW is plotted as mapped |E|, a drift-related E x B diagnostic rather than direct ion speed.",
        fontsize=7.8,
        ha="left",
        va="bottom",
    )
    out = ROOT / "guvi_on2_20150317_global_subauroral_drift_overlay.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def summarize_band_points(name, hemi, mlat, value, ut=None, units=""):
    lower, upper = SUBAURORAL_ABS_MLAT
    if hemi == "N":
        mask = (mlat >= lower) & (mlat <= upper)
    else:
        mask = (mlat <= -lower) & (mlat >= -upper)
    mask &= np.isfinite(value)
    if not np.any(mask):
        return f"- {name} {hemi}: n=0"
    selected = value[mask]
    ut_text = ""
    if ut is not None:
        ut_text = f", UT={np.nanmin(ut[mask]):.2f}-{np.nanmax(ut[mask]):.2f}"
    return (
        f"- {name} {hemi}: n={int(mask.sum())}{ut_text}, "
        f"median={np.nanmedian(selected):.3g}, p95={np.nanpercentile(selected, 95):.3g}, "
        f"max={np.nanmax(selected):.3g} {units}".rstrip()
    )


def write_summary(path, grid, guvi_raw, dmsp, rbsp_records, themis_records):
    lines = ["17 Mar 2015 GUVI O/N2 global subauroral drift-overlay summary", ""]
    finite_grid = grid[np.isfinite(grid)]
    lines.append(
        f"GUVI observed/interpolated grid: finite cells={len(finite_grid)}, "
        f"median={np.nanmedian(finite_grid):.3f}, min={np.nanmin(finite_grid):.3f}, max={np.nanmax(finite_grid):.3f}"
    )
    lines.append(
        f"GUVI raw swath: n={len(guvi_raw['on2'])}, "
        f"UT={np.nanmin(guvi_raw['ut']):.2f}-{np.nanmax(guvi_raw['ut']):.2f}, "
        f"median O/N2={np.nanmedian(guvi_raw['on2']):.3f}"
    )
    lines.append("")
    lines.append("Subauroral bands use centered-dipole |MLAT|=48-70 deg.")
    for hemi in ["N", "S"]:
        lines.append(summarize_band_points("GUVI raw O/N2", hemi, guvi_raw["mlat"], guvi_raw["on2"], guvi_raw["ut"]))
    lines.append("")
    lines.append("Drift-related overlays inside the subauroral bands:")
    dmsp_speed = np.abs(dmsp["horizontal_ion_drift_mps"]) / 1000.0
    for hemi in ["N", "S"]:
        lines.append(summarize_band_points("DMSP SSIES |Vi|", hemi, dmsp["cd_mlat"], dmsp_speed, dmsp["ut"], "km/s"))
    rbsp_by_hemi = {}
    for rec in rbsp_records:
        rbsp_by_hemi.setdefault(rec["hemi"], []).append(rec)
    for hemi in ["N", "S"]:
        records = rbsp_by_hemi.get(hemi, [])
        if not records:
            lines.append(f"- RBSP mapped |E| {hemi}: n=0")
            continue
        mlat = np.concatenate([rec["mlat"] for rec in records])
        value = np.concatenate([rec["value"] for rec in records])
        ut = np.concatenate([rec["ut"] for rec in records])
        lines.append(summarize_band_points("RBSP mapped |E|", hemi, mlat, value, ut, "mV/m"))
    themis_by_hemi = {}
    for rec in themis_records:
        themis_by_hemi.setdefault(rec["hemi"], []).append(rec)
    for hemi in ["N", "S"]:
        records = themis_by_hemi.get(hemi, [])
        if not records:
            lines.append(f"- THEMIS mapped ion |V| {hemi}: n=0")
            continue
        mlat = np.concatenate([rec["mlat"] for rec in records])
        value = np.concatenate([rec["value"] for rec in records])
        ut = np.concatenate([rec["ut"] for rec in records])
        lines.append(summarize_band_points("THEMIS mapped ion |V|", hemi, mlat, value, ut, "km/s"))
    lines.append("")
    lines.append(
        "Swarm EFI/TIE drift is not included because no local Swarm drift CDF was found; local Swarm MAG files are orbit/magnetic-field tracks only."
    )
    lines.append(
        "Caveat: CD-MLAT bands and THEMIS footpoints are screening-level centered-dipole approximations; RBSP footpoints use the local MagEphem files."
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    lon, lat, grid = read_guvi_observed_grid(GUVI_FILES["17 Mar"])
    guvi_raw = read_guvi_raw_points(GUVI_FILES["17 Mar"])
    dmsp = read_dmsp()
    rbsp_records = read_rbsp_mapped()
    themis_records = read_themis_mapped()
    lon2, lat2, mlat2 = magnetic_latitude_mesh()

    base_out = plot_base_map(lon, lat, grid, lon2, lat2, mlat2)
    overlay_out = plot_overlay_map(lon, lat, grid, lon2, lat2, mlat2, dmsp, rbsp_records, themis_records)
    summary_out = ROOT / "guvi_on2_20150317_global_subauroral_drift_overlay_summary.txt"
    write_summary(summary_out, grid, guvi_raw, dmsp, rbsp_records, themis_records)
    print(base_out)
    print(overlay_out)
    print(summary_out)


if __name__ == "__main__":
    main()

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.lines import Line2D
from netCDF4 import Dataset
import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE = SCRIPT_DIR.parent.parent
DATA_DIR = SCRIPT_DIR / "data"
GUVI_FILE = WORKSPACE / "timed_guvi_l3-on2_2015076_Av0100r000.nc"

sys.path.insert(0, str(SCRIPT_DIR.parent / ".codex_deps"))
sys.path.insert(0, str(WORKSPACE))
from make_guvi_dmsp_westward_saps_window import read_guvi_raw_cd  # noqa: E402
from make_guvi_dmsp_mlt_candidate import centered_dipole_coords  # noqa: E402


BOUNDARY_LAT = 45.0
PLOT_HEMI = "S"
TARGET_UT = 22.5


@dataclass
class SsusiOrbit:
    path: Path
    sat: str
    rev: str
    start: datetime
    stop: datetime
    image_time: datetime
    mlat: np.ndarray
    mlon: np.ndarray
    mlt: np.ndarray
    ut: np.ndarray
    lbhs: np.ndarray
    score: int


def cmap_jhuapl_ssusi_like() -> LinearSegmentedColormap:
    # This is the DMSP/SSUSI-style colormap provided by GeospaceLAB
    # in geospacelab.visualization.mpl.colormaps.cmap_jhuapl_ssusi_like.
    colors = [
        "#000000",
        "#330066",
        "#0000CC",
        "#0080FF",
        "#00CC00",
        "#80FF00",
        "#FFFF00",
        "#FF8000",
        "#FF0000",
        "#FF6666",
    ]
    return LinearSegmentedColormap.from_list("jhuapl_ssusi_like", colors, N=500)


def cmap_aurora_geospacelab() -> LinearSegmentedColormap:
    # This is the default aurora colormap used by GeospaceLAB's DMSP/SSUSI
    # EDR-Aurora variable configuration.
    colors = [
        "#AEAAB0",
        "#78519A",
        "#51227B",
        "#310073",
        "#000073",
        "#004373",
        "#005B73",
        "#007365",
        "#00733A",
        "#007300",
        "#009900",
        "#00BB00",
        "#00DD00",
        "#00FF00",
        "#80FF80",
        "#B3FFB3",
    ]
    return LinearSegmentedColormap.from_list("geospacelab_aurora", colors, N=500)


def parse_ydoy(text: str) -> datetime:
    return datetime(int(text[:4]), 1, 1) + timedelta(
        days=int(text[4:7]) - 1,
        hours=int(text[8:10]),
        minutes=int(text[10:12]),
        seconds=int(text[12:14]),
    )


def decimal_ut_to_datetime(year: int, doy: int, ut_hour: float) -> datetime:
    return datetime(year, 1, 1) + timedelta(days=doy - 1, hours=float(ut_hour))


def polar_xy(
    mlt: np.ndarray,
    mlat: np.ndarray,
    boundary_lat: float = BOUNDARY_LAT,
    mask_outside: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    radius = 90.0 - np.abs(mlat)
    theta = np.pi / 2.0 - (mlt / 24.0) * 2.0 * np.pi
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    radius_limit = 90.0 - boundary_lat
    if mask_outside:
        outside = radius > radius_limit
        x = np.where(outside, np.nan, x)
        y = np.where(outside, np.nan, y)
    return x, y


def read_ssusi_south(path: Path) -> SsusiOrbit:
    match = re.search(
        r"dmsp(?P<sat>f\d+)_ssusi_edr-aurora_(?P<start>\d{7}T\d{6})-(?P<stop>\d{7}T\d{6})-REV(?P<rev>\d+)_",
        path.name,
    )
    if not match:
        raise ValueError(f"Cannot parse SSUSI file name: {path.name}")

    with Dataset(path) as ds:
        start = datetime.strptime(ds.STARTING_TIME, "%Y%j%H%M%S")
        stop = datetime.strptime(ds.STOPPING_TIME, "%Y%j%H%M%S")
        mlat = -np.asarray(ds.variables["LATITUDE_GEOMAGNETIC_GRID_MAP"][:], dtype=float)
        mlon = np.asarray(ds.variables["LONGITUDE_GEOMAGNETIC_SOUTH_GRID_MAP"][:], dtype=float)
        mlt = np.asarray(ds.variables["MLT_GRID_MAP"][:], dtype=float)
        ut = np.asarray(ds.variables["UT_S"][:], dtype=float)
        lbhs = np.asarray(ds.variables["DISK_RADIANCEDATA_INTENSITY_SOUTH"][3, :, :], dtype=float)

    invalid = (ut <= 0) | ~np.isfinite(lbhs) | (lbhs <= 0)
    lbhs = lbhs.copy()
    lbhs[invalid] = np.nan

    valid_lat = mlat.copy()
    valid_lat[invalid] = np.nan
    valid_ut = ut[np.isfinite(lbhs)]
    if valid_ut.size:
        image_ut = float(np.nanmedian(valid_ut))
        image_time = decimal_ut_to_datetime(start.year, int(start.strftime("%j")), image_ut)
    else:
        image_time = start + (stop - start) / 2

    overlap_roi = (
        np.isfinite(lbhs)
        & (mlat <= -45.0)
        & (mlat >= -75.0)
        & (mlt >= 10.0)
        & (mlt <= 18.0)
    )
    score = int(np.count_nonzero(overlap_roi))

    return SsusiOrbit(
        path=path,
        sat=match.group("sat").upper(),
        rev=match.group("rev"),
        start=start,
        stop=stop,
        image_time=image_time,
        mlat=mlat,
        mlon=mlon,
        mlt=mlt,
        ut=ut,
        lbhs=lbhs,
        score=score,
    )


def draw_polar_grid(ax: plt.Axes, boundary_lat: float = BOUNDARY_LAT) -> None:
    radius_limit = 90.0 - boundary_lat
    background = plt.Circle((0.0, 0.0), radius_limit, facecolor="#faf8f2", edgecolor="none", zorder=0)
    ax.add_patch(background)
    phi = np.linspace(0, 2 * np.pi, 500)
    for lat in [50, 60, 70, 80]:
        radius = 90.0 - lat
        if radius > radius_limit:
            continue
        ax.plot(radius * np.cos(phi), radius * np.sin(phi), color="#4a2c18", lw=0.55, ls=":", alpha=0.75, zorder=1)
        ax.text(0.4, radius + 0.6, f"{-lat:d}", color="0.35", fontsize=7.5, ha="left", va="bottom")
    ax.plot(radius_limit * np.cos(phi), radius_limit * np.sin(phi), color="black", lw=0.9, zorder=2)

    for mlt in range(0, 24, 3):
        theta = np.pi / 2.0 - (mlt / 24.0) * 2.0 * np.pi
        ax.plot(
            [0, radius_limit * np.cos(theta)],
            [0, radius_limit * np.sin(theta)],
            color="#4a2c18",
            lw=0.45,
            ls=":",
            alpha=0.72,
            zorder=1,
        )
    for mlt, label in [(0, "00"), (6, "06"), (12, "12"), (18, "18")]:
        theta = np.pi / 2.0 - (mlt / 24.0) * 2.0 * np.pi
        ax.text(
            (radius_limit + 3.2) * np.cos(theta),
            (radius_limit + 3.2) * np.sin(theta),
            label,
            ha="center",
            va="center",
            fontsize=8.5,
            color="0.25",
        )

    ax.set_aspect("equal")
    ax.set_xlim(-radius_limit - 8, radius_limit + 8)
    ax.set_ylim(-radius_limit - 8, radius_limit + 8)
    ax.axis("off")
    ax.text(0.0, radius_limit + 6.6, "MLT", ha="center", va="bottom", fontsize=8.3, color="0.32")


def overlay_centered_dipole_coastlines(ax: plt.Axes, doy: float) -> bool:
    try:
        import cartopy
        import cartopy.io.shapereader as shpreader
    except Exception:
        return False

    cartopy.config["data_dir"] = str(SCRIPT_DIR / "cartopy_data")
    try:
        land_path = shpreader.natural_earth(resolution="110m", category="physical", name="land")
        reader = shpreader.Reader(land_path)
    except Exception:
        return False

    radius_limit = 90.0 - BOUNDARY_LAT
    for geom in reader.geometries():
        polygons = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
        for polygon in polygons:
            lon, lat = np.asarray(polygon.exterior.coords.xy[0]), np.asarray(polygon.exterior.coords.xy[1])
            if len(lon) < 3:
                continue
            mlat, mlt = centered_dipole_coords(lat, lon, np.full_like(lat, doy, dtype=float))
            x, y = polar_xy(mlt, mlat)
            valid = np.isfinite(x) & np.isfinite(y)
            if np.count_nonzero(valid) < 2:
                continue
            start = None
            for i, ok in enumerate(valid):
                if ok and start is None:
                    start = i
                if start is not None and (not ok or i == len(valid) - 1):
                    stop = i if not ok else i + 1
                    if stop - start >= 2:
                        sx = x[start:stop]
                        sy = y[start:stop]
                        jumps = np.hypot(np.diff(sx), np.diff(sy))
                        cuts = np.where(jumps > radius_limit * 0.45)[0] + 1
                        for piece_x, piece_y in zip(np.split(sx, cuts), np.split(sy, cuts)):
                            if len(piece_x) >= 2:
                                ax.plot(piece_x, piece_y, color="0.55", lw=0.45, alpha=0.75, zorder=2)
                    start = None
    return True


def plot_ssusi_guvi(selected: SsusiOrbit, guvi: dict[str, np.ndarray], out_path: Path) -> dict[str, object]:
    cmap_ssusi = cmap_aurora_geospacelab()
    cmap_ssusi.set_bad((1, 1, 1, 0))

    x, y = polar_xy(selected.mlt, selected.mlat, mask_outside=False)
    visible = np.isfinite(selected.lbhs) & (selected.mlat <= -BOUNDARY_LAT)

    guvi_mask = (
        (guvi["ut"] >= 22.0)
        & (guvi["ut"] <= 22.68)
        & (guvi["mlat"] <= -BOUNDARY_LAT)
        & (guvi["mlat"] >= -75.0)
        & (guvi["mlt"] >= 10.5)
        & (guvi["mlt"] <= 18.3)
        & np.isfinite(guvi["on2"])
    )
    guvi_idx = np.where(guvi_mask)[0]
    guvi_idx = guvi_idx[np.argsort(guvi["ut"][guvi_idx])]
    gx, gy = polar_xy(guvi["mlt"][guvi_idx], guvi["mlat"][guvi_idx])

    fig = plt.figure(figsize=(7.2, 7.0), dpi=220)
    ax = fig.add_axes([0.08, 0.08, 0.72, 0.82])
    draw_polar_grid(ax)
    coastlines_added = overlay_centered_dipole_coastlines(ax, 76.0 + TARGET_UT / 24.0)

    mesh = ax.pcolormesh(
        x,
        y,
        np.where(visible, selected.lbhs, np.nan),
        shading="auto",
        cmap=cmap_ssusi,
        norm=LogNorm(vmin=10, vmax=6000),
        alpha=0.82,
        zorder=3,
    )

    ssusi_ut_min = float(np.nanmin(selected.ut[visible]))
    ssusi_ut_max = float(np.nanmax(selected.ut[visible]))
    guvi_ut_min = float(np.nanmin(guvi["ut"][guvi_idx])) if len(guvi_idx) else np.nan
    guvi_ut_max = float(np.nanmax(guvi["ut"][guvi_idx])) if len(guvi_idx) else np.nan

    if len(gx) > 1:
        ax.plot(gx, gy, color="white", lw=5.0, alpha=0.9, zorder=8, solid_capstyle="round")
        ax.plot(gx, gy, color="black", lw=2.1, alpha=0.96, zorder=9, solid_capstyle="round")
    guvi_scatter = ax.scatter(
        gx,
        gy,
        c=guvi["on2"][guvi_idx],
        s=23,
        cmap="turbo_r",
        vmin=0.12,
        vmax=0.65,
        edgecolors="black",
        linewidths=0.25,
        zorder=10,
    )

    common = (
        guvi_mask
        & (guvi["ut"] >= np.nanmin(selected.ut[visible]))
        & (guvi["ut"] <= np.nanmax(selected.ut[visible]))
    )
    if np.any(common):
        common_idx = np.where(common)[0]
        cx, cy = polar_xy(guvi["mlt"][common_idx], guvi["mlat"][common_idx])
        ax.scatter(cx, cy, s=38, facecolors="none", edgecolors="white", linewidths=0.8, zorder=11)

    ax.set_title(
        f"DMSP/SSUSI LBHS {selected.sat} South with TIMED/GUVI O/N2 Track, REV {selected.rev}\n"
        f"17 Mar 2015; SSUSI south UT {ssusi_ut_min:.2f}-{ssusi_ut_max:.2f}; GUVI UT {guvi_ut_min:.2f}-{guvi_ut_max:.2f}",
        fontsize=11.2,
        pad=10,
    )

    cax1 = fig.add_axes([0.84, 0.29, 0.035, 0.44])
    cbar1 = fig.colorbar(mesh, cax=cax1, extend="max")
    cbar1.set_label("SSUSI LBHS (R)", fontsize=8.2)
    cbar1.ax.tick_params(labelsize=7.2)

    cax2 = fig.add_axes([0.91, 0.29, 0.035, 0.44])
    cbar2 = fig.colorbar(guvi_scatter, cax=cax2)
    cbar2.set_label("GUVI O/N2", fontsize=8.2)
    cbar2.ax.tick_params(labelsize=7.2)

    legend_handles = [
        Line2D([0], [0], color="black", lw=2.1, label="GUVI track"),
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor="none",
            markeredgecolor="0.25",
            lw=0,
            label="GUVI within SSUSI UT",
        ),
    ]
    ax.legend(handles=legend_handles, loc="lower left", bbox_to_anchor=(0.05, 0.02), fontsize=7.8, frameon=False)

    fig.text(
        0.08,
        0.018,
        "GeospaceLAB default SSUSI LBHS style; coastline and GUVI MLAT/MLT use local centered-dipole transform.",
        fontsize=7.4,
        color="0.35",
    )

    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    return {
        "selected_sat": selected.sat,
        "selected_rev": selected.rev,
        "selected_file": selected.path.name,
        "selected_start": selected.start,
        "selected_stop": selected.stop,
        "selected_image_time": selected.image_time,
        "ssusi_valid_ut_min": ssusi_ut_min,
        "ssusi_valid_ut_max": ssusi_ut_max,
        "ssusi_visible_pixels": int(np.count_nonzero(visible)),
        "guvi_points": int(len(guvi_idx)),
        "guvi_common_ut_points": int(np.count_nonzero(common)),
        "guvi_ut_min": guvi_ut_min,
        "guvi_ut_max": guvi_ut_max,
        "guvi_mlat_min": float(np.nanmin(guvi["mlat"][guvi_idx])) if len(guvi_idx) else np.nan,
        "guvi_mlat_max": float(np.nanmax(guvi["mlat"][guvi_idx])) if len(guvi_idx) else np.nan,
        "guvi_mlt_min": float(np.nanmin(guvi["mlt"][guvi_idx])) if len(guvi_idx) else np.nan,
        "guvi_mlt_max": float(np.nanmax(guvi["mlt"][guvi_idx])) if len(guvi_idx) else np.nan,
        "guvi_on2_p05": float(np.nanpercentile(guvi["on2"][guvi_idx], 5)) if len(guvi_idx) else np.nan,
        "guvi_on2_med": float(np.nanmedian(guvi["on2"][guvi_idx])) if len(guvi_idx) else np.nan,
        "coastlines_added": coastlines_added,
    }


def write_summary(path: Path, selected: SsusiOrbit, orbits: list[SsusiOrbit], info: dict[str, object]) -> None:
    lines = [
        "DMSP/SSUSI + TIMED/GUVI overlay, 17 Mar 2015",
        "",
        "GeospaceLAB reference choices:",
        "- DMSP/SSUSI EDR-Aurora product",
        "- LBHS emission channel",
        "- GeospaceLAB default SSUSI/aurora colormap",
        "- light polar-map background and coastline overlay, matching the repository example more closely",
        "- log color scale with limits 10-6000 R",
        "- magnetic polar map in MLT/MLAT",
        "",
        "Downloaded target-orbit files:",
    ]
    for orbit in orbits:
        valid = np.isfinite(orbit.lbhs) & (orbit.mlat <= -BOUNDARY_LAT)
        lines.append(
            f"- {orbit.sat} REV {orbit.rev}: {orbit.start:%H:%M:%S}-{orbit.stop:%H:%M:%S} UT, "
            f"south valid UT {np.nanmin(orbit.ut[valid]):.2f}-{np.nanmax(orbit.ut[valid]):.2f}, "
            f"overlap-score pixels={orbit.score}, file={orbit.path.name}"
        )
    lines.extend(
        [
            "",
            "Selected main panel:",
            f"- {selected.sat} REV {selected.rev}; selected because it has the largest valid SSUSI south-hemisphere coverage in the GUVI MLT/MLAT sector.",
            f"- File: {selected.path.name}",
            f"- SSUSI south valid UT range: {info['ssusi_valid_ut_min']:.2f}-{info['ssusi_valid_ut_max']:.2f}.",
            f"- SSUSI median valid-south-pixel time: {selected.image_time:%Y-%m-%d %H:%M UT}.",
            f"- Visible SSUSI pixels above {BOUNDARY_LAT:.0f} deg magnetic latitude: {info['ssusi_visible_pixels']}",
            "",
            "GUVI overlay:",
            f"- Points: {info['guvi_points']} in 22.00-22.68 UT, MLAT -75 to -45, MLT 10.5-18.3.",
            f"- Common-UT highlighted points: {info['guvi_common_ut_points']} within SSUSI valid UT {info['ssusi_valid_ut_min']:.2f}-{info['ssusi_valid_ut_max']:.2f}.",
            f"- GUVI UT range: {info['guvi_ut_min']:.2f}-{info['guvi_ut_max']:.2f}.",
            f"- GUVI MLAT range: {info['guvi_mlat_min']:.2f} to {info['guvi_mlat_max']:.2f}; MLT range: {info['guvi_mlt_min']:.2f}-{info['guvi_mlt_max']:.2f}.",
            f"- GUVI O/N2 p05/median: {info['guvi_on2_p05']:.3f}/{info['guvi_on2_med']:.3f}.",
            f"- Coastline overlay added: {info['coastlines_added']}.",
            "",
            "Caveat:",
            "- SSUSI MLAT/MLT come from the product grid; GUVI MLAT/MLT use the existing local centered-dipole screening transform, not AACGMV2.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    paths = sorted(DATA_DIR.glob("dmspf*_ssusi_edr-aurora_*.nc"))
    if not paths:
        raise FileNotFoundError(f"No DMSP/SSUSI NetCDF files found in {DATA_DIR}")
    orbits = [read_ssusi_south(path) for path in paths]
    selected = max(orbits, key=lambda item: item.score)

    guvi = read_guvi_raw_cd(GUVI_FILE)
    out_png = SCRIPT_DIR / "dmsp_ssusi_lbhs_guvi_track_20150317_south_geospacelab_demo_style.png"
    info = plot_ssusi_guvi(selected, guvi, out_png)
    out_txt = SCRIPT_DIR / "dmsp_ssusi_lbhs_guvi_track_20150317_south_geospacelab_demo_style_summary.txt"
    write_summary(out_txt, selected, orbits, info)
    print(f"Saved {out_png}")
    print(f"Saved {out_txt}")


if __name__ == "__main__":
    main()

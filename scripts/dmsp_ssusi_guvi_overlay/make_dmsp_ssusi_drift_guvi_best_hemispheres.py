from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
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
from make_guvi_dmsp_mlt_candidate import centered_dipole_coords, read_dmsp  # noqa: E402
from make_guvi_dmsp_westward_saps_window import read_guvi_raw_cd  # noqa: E402


BOUNDARY_LAT = 45.0
DRIFT_LIMIT_KMS = 3.0
DMSP_ARROW_SCALE = 2.6
DMSP_PURPLE = "#7a1688"


@dataclass
class SsusiOrbit:
    path: Path
    sat: str
    rev: str
    start: datetime
    stop: datetime
    hemi: str
    mlat: np.ndarray
    mlon: np.ndarray
    mlt: np.ndarray
    ut: np.ndarray
    lbhs: np.ndarray
    visible: np.ndarray
    score: float

    @property
    def ut_min(self) -> float:
        return float(np.nanmin(self.ut[self.visible]))

    @property
    def ut_max(self) -> float:
        return float(np.nanmax(self.ut[self.visible]))


def cmap_aurora_geospacelab() -> LinearSegmentedColormap:
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


def polar_xy(
    mlt: np.ndarray,
    mlat: np.ndarray,
    boundary_lat: float = BOUNDARY_LAT,
    mask_outside: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    radius = 90.0 - np.abs(mlat)
    # GeospaceLAB-style MLT orientation: 12 MLT at top, 06 at right,
    # 00 at bottom, and 18 at left.
    theta = np.pi / 2.0 + ((mlt - 12.0) / 24.0) * 2.0 * np.pi
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    if mask_outside:
        outside = radius > 90.0 - boundary_lat
        x = np.where(outside, np.nan, x)
        y = np.where(outside, np.nan, y)
    return x, y


def read_ssusi(path: Path, hemi: str, dmsp: dict[str, np.ndarray], guvi: dict[str, np.ndarray]) -> SsusiOrbit:
    match = re.search(
        r"dmsp(?P<sat>f\d+)_ssusi_edr-aurora_.*-REV(?P<rev>\d+)_",
        path.name,
    )
    if not match:
        raise ValueError(f"Cannot parse SSUSI file name: {path.name}")
    sat = match.group("sat").upper()
    pole = "NORTH" if hemi == "N" else "SOUTH"

    with Dataset(path) as ds:
        start = datetime.strptime(ds.STARTING_TIME, "%Y%j%H%M%S")
        stop = datetime.strptime(ds.STOPPING_TIME, "%Y%j%H%M%S")
        base_mlat = np.asarray(ds.variables["LATITUDE_GEOMAGNETIC_GRID_MAP"][:], dtype=float)
        mlat = base_mlat if hemi == "N" else -base_mlat
        mlon_name = f"LONGITUDE_GEOMAGNETIC_{pole}_GRID_MAP"
        mlon = np.asarray(ds.variables[mlon_name][:], dtype=float)
        mlt = np.asarray(ds.variables["MLT_GRID_MAP"][:], dtype=float)
        ut = np.asarray(ds.variables[f"UT_{hemi}"][:], dtype=float)
        lbhs = np.asarray(ds.variables[f"DISK_RADIANCEDATA_INTENSITY_{pole}"][3, :, :], dtype=float)

    invalid = (ut <= 0) | ~np.isfinite(lbhs) | (lbhs <= 0)
    lbhs = lbhs.copy()
    lbhs[invalid] = np.nan
    if hemi == "N":
        visible = np.isfinite(lbhs) & (mlat >= BOUNDARY_LAT)
        hemi_mask = lambda arr: arr >= BOUNDARY_LAT
    else:
        visible = np.isfinite(lbhs) & (mlat <= -BOUNDARY_LAT)
        hemi_mask = lambda arr: arr <= -BOUNDARY_LAT

    if not np.any(visible):
        score = -np.inf
    else:
        umin, umax = float(np.nanmin(ut[visible])), float(np.nanmax(ut[visible]))
        dm = (
            (dmsp["satellite"] == sat)
            & (dmsp["ut"] >= umin - 0.15)
            & (dmsp["ut"] <= umax + 0.15)
            & hemi_mask(dmsp["cd_mlat"])
        )
        gm = (
            (guvi["ut"] >= umin - 0.35)
            & (guvi["ut"] <= umax + 0.35)
            & hemi_mask(guvi["mlat"])
        )
        drift_kms = np.abs(dmsp["horizontal_ion_drift_mps"][dm]) / 1000.0
        p95 = float(np.nanpercentile(drift_kms, 95)) if drift_kms.size else 0.0
        score = (
            min(int(np.count_nonzero(dm)), 1800) * 0.20
            + min(int(np.count_nonzero(gm)), 400) * 0.55
            + min(int(np.count_nonzero(visible)), 26000) * 0.006
            + p95 * 80.0
        )

    return SsusiOrbit(
        path=path,
        sat=sat,
        rev=match.group("rev"),
        start=start,
        stop=stop,
        hemi=hemi,
        mlat=mlat,
        mlon=mlon,
        mlt=mlt,
        ut=ut,
        lbhs=lbhs,
        visible=visible,
        score=score,
    )


def draw_polar_grid(ax: plt.Axes, hemi: str) -> None:
    radius_limit = 90.0 - BOUNDARY_LAT
    ax.add_patch(plt.Circle((0.0, 0.0), radius_limit, facecolor="#faf8f2", edgecolor="none", zorder=0))
    phi = np.linspace(0, 2 * np.pi, 500)
    for lat in [50, 60, 70, 80]:
        radius = 90.0 - lat
        ax.plot(radius * np.cos(phi), radius * np.sin(phi), color="#4a2c18", lw=0.55, ls=":", alpha=0.74, zorder=1)
        label = f"{lat:d}{hemi}"
        ax.text(0.5, radius + 0.6, label, color="0.34", fontsize=7.2, ha="left", va="bottom")
    ax.plot(radius_limit * np.cos(phi), radius_limit * np.sin(phi), color="black", lw=0.85, zorder=2)

    for mlt in range(0, 24, 3):
        theta = np.pi / 2.0 + ((mlt - 12.0) / 24.0) * 2.0 * np.pi
        ax.plot([0, radius_limit * np.cos(theta)], [0, radius_limit * np.sin(theta)], color="#4a2c18", lw=0.45, ls=":", alpha=0.72, zorder=1)
    for mlt, label in [(12, "12"), (6, "06"), (0, "00"), (18, "18")]:
        theta = np.pi / 2.0 + ((mlt - 12.0) / 24.0) * 2.0 * np.pi
        ax.text((radius_limit + 3.4) * np.cos(theta), (radius_limit + 3.4) * np.sin(theta), label, ha="center", va="center", fontsize=8.8, color="0.22")

    ax.text(0.0, radius_limit + 6.4, "MLT", ha="center", va="bottom", fontsize=8.0, color="0.32")
    ax.set_aspect("equal")
    ax.set_xlim(-radius_limit - 8, radius_limit + 8)
    ax.set_ylim(-radius_limit - 8, radius_limit + 8)
    ax.axis("off")


def overlay_centered_dipole_coastlines(ax: plt.Axes, hemi: str, doy: float) -> bool:
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
            hemi_ok = mlat >= BOUNDARY_LAT if hemi == "N" else mlat <= -BOUNDARY_LAT
            x, y = polar_xy(mlt, mlat)
            valid = np.isfinite(x) & np.isfinite(y) & hemi_ok
            if np.count_nonzero(valid) < 2:
                continue
            start = None
            for i, ok in enumerate(valid):
                if ok and start is None:
                    start = i
                if start is not None and (not ok or i == len(valid) - 1):
                    stop = i if not ok else i + 1
                    if stop - start >= 2:
                        sx, sy = x[start:stop], y[start:stop]
                        jumps = np.hypot(np.diff(sx), np.diff(sy))
                        cuts = np.where(jumps > radius_limit * 0.45)[0] + 1
                        for px, py in zip(np.split(sx, cuts), np.split(sy, cuts)):
                            if len(px) >= 2:
                                ax.plot(px, py, color="0.56", lw=0.42, alpha=0.70, zorder=2)
                    start = None
    return True


def split_xy(x: np.ndarray, y: np.ndarray, max_jump: float = 12.0) -> list[tuple[np.ndarray, np.ndarray]]:
    valid = np.isfinite(x) & np.isfinite(y)
    idx = np.where(valid)[0]
    if idx.size == 0:
        return []
    groups: list[tuple[np.ndarray, np.ndarray]] = []
    start = 0
    vx, vy = x[idx], y[idx]
    for i in range(1, len(idx)):
        if idx[i] != idx[i - 1] + 1 or np.hypot(vx[i] - vx[i - 1], vy[i] - vy[i - 1]) > max_jump:
            groups.append((vx[start:i], vy[start:i]))
            start = i
    groups.append((vx[start:], vy[start:]))
    return groups


def draw_drift_sticks(ax: plt.Axes, x: np.ndarray, y: np.ndarray, drift_kms: np.ndarray, step: int = 22) -> None:
    if len(x) < 5:
        return
    xy_disp = ax.transData.transform(np.column_stack([x, y]))
    tangent = np.gradient(xy_disp, axis=0)
    norm = np.hypot(tangent[:, 0], tangent[:, 1])
    ok = norm > 0
    tangent[ok] /= norm[ok, None]
    normal = np.column_stack([-tangent[:, 1], tangent[:, 0]])
    for pos in range(3, len(x) - 3, max(step, 1)):
        speed = drift_kms[pos]
        if not np.isfinite(speed) or abs(speed) < 0.15:
            continue
        length_px = np.clip(speed, -DRIFT_LIMIT_KMS, DRIFT_LIMIT_KMS) / DRIFT_LIMIT_KMS * 16.0
        start = xy_disp[pos]
        end = start + normal[pos] * length_px
        end_data = ax.transData.inverted().transform(end)
        color = "#b2182b" if speed >= 0 else "#2166ac"
        ax.annotate(
            "",
            xy=end_data,
            xytext=(x[pos], y[pos]),
            arrowprops=dict(arrowstyle="-|>", color=color, lw=0.45, mutation_scale=3.2, shrinkA=0, shrinkB=0, alpha=0.50),
            zorder=12,
        )


def draw_dmsp_velocity_quiver(
    ax: plt.Axes,
    x: np.ndarray,
    y: np.ndarray,
    glat: np.ndarray,
    glon: np.ndarray,
    drift_kms: np.ndarray,
    step: int,
):
    """Project DMSP horizontal ion drift into polar-map arrows.

    This follows the structure in DMSP_vi.m: first estimate the westward
    component from the along-track latitude/longitude differences, then
    project that signed component perpendicular to the displayed track.
    The quiver scale is set so arrow length is proportional to km/s.
    """
    if len(x) < 5:
        return None
    lon_unwrapped = np.rad2deg(np.unwrap(np.deg2rad(glon)))
    dlat = np.gradient(glat)
    dlon = np.gradient(lon_unwrapped)
    dr_geo = np.hypot(dlat, dlon)
    vwest = np.divide(drift_kms * dlat, dr_geo, out=np.full_like(drift_kms, np.nan), where=dr_geo > 0)

    dx = np.gradient(x)
    dy = np.gradient(y)
    dr_xy = np.hypot(dx, dy)
    ux = np.divide(vwest * dy, dr_xy, out=np.full_like(vwest, np.nan), where=dr_xy > 0)
    uy = np.divide(vwest * dx, dr_xy, out=np.full_like(vwest, np.nan), where=dr_xy > 0)

    valid = np.isfinite(x) & np.isfinite(y) & np.isfinite(ux) & np.isfinite(uy)
    valid &= np.abs(drift_kms) >= 0.15
    positions = np.where(valid)[0][:: max(step, 1)]
    if len(positions) == 0:
        return None
    q = ax.quiver(
        x[positions],
        y[positions],
        ux[positions],
        uy[positions],
        angles="xy",
        scale_units="xy",
        scale=1.0 / DMSP_ARROW_SCALE,
        color=DMSP_PURPLE,
        width=0.0030,
        headwidth=3.6,
        headlength=4.6,
        headaxislength=4.0,
        alpha=0.76,
        zorder=12,
    )
    ax.quiverkey(
        q,
        X=0.84,
        Y=0.90,
        U=1.0,
        label="1 km/s",
        labelpos="E",
        coordinates="axes",
        fontproperties={"size": 7.2},
        color=DMSP_PURPLE,
    )
    return q


def select_dmsp_track(orbit: SsusiOrbit, dmsp: dict[str, np.ndarray]) -> np.ndarray:
    hemi_mask = dmsp["cd_mlat"] >= BOUNDARY_LAT if orbit.hemi == "N" else dmsp["cd_mlat"] <= -BOUNDARY_LAT
    return (
        (dmsp["satellite"] == orbit.sat)
        & (dmsp["ut"] >= orbit.ut_min - 0.15)
        & (dmsp["ut"] <= orbit.ut_max + 0.15)
        & hemi_mask
        & np.isfinite(dmsp["horizontal_ion_drift_mps"])
    )


def select_guvi_track(orbit: SsusiOrbit, guvi: dict[str, np.ndarray]) -> np.ndarray:
    hemi_mask = guvi["mlat"] >= BOUNDARY_LAT if orbit.hemi == "N" else guvi["mlat"] <= -BOUNDARY_LAT
    return (
        (guvi["ut"] >= orbit.ut_min - 0.35)
        & (guvi["ut"] <= orbit.ut_max + 0.35)
        & hemi_mask
        & np.isfinite(guvi["on2"])
    )


def plot_panel(
    ax: plt.Axes,
    orbit: SsusiOrbit,
    dmsp: dict[str, np.ndarray],
    guvi: dict[str, np.ndarray],
    ssusi_cmap: LinearSegmentedColormap,
) -> tuple[object, object, dict[str, object]]:
    draw_polar_grid(ax, orbit.hemi)
    coast = overlay_centered_dipole_coastlines(ax, orbit.hemi, 76.0 + (orbit.ut_min + orbit.ut_max) / 48.0)
    x, y = polar_xy(orbit.mlt, orbit.mlat, mask_outside=False)
    ssusi_mesh = ax.pcolormesh(
        x,
        y,
        np.where(orbit.visible, orbit.lbhs, np.nan),
        shading="auto",
        cmap=ssusi_cmap,
        norm=LogNorm(vmin=10, vmax=6000),
        alpha=0.83,
        zorder=3,
    )

    dm = select_dmsp_track(orbit, dmsp)
    dm_idx = np.where(dm)[0]
    dm_idx = dm_idx[np.argsort(dmsp["ut"][dm_idx])]
    dx, dy = polar_xy(dmsp["cd_mlt"][dm_idx], dmsp["cd_mlat"][dm_idx])
    drift_kms = dmsp["horizontal_ion_drift_mps"][dm_idx] / 1000.0
    for sx, sy in split_xy(dx, dy):
        ax.plot(sx, sy, color="white", lw=3.0, alpha=0.72, zorder=9)
        ax.plot(sx, sy, color=DMSP_PURPLE, lw=1.35, alpha=0.88, zorder=10)
    draw_dmsp_velocity_quiver(
        ax,
        dx,
        dy,
        dmsp["glat"][dm_idx],
        dmsp["glon"][dm_idx],
        drift_kms,
        step=max(18, len(dx) // 42),
    )

    gm = select_guvi_track(orbit, guvi)
    guvi_idx = np.where(gm)[0]
    guvi_idx = guvi_idx[np.argsort(guvi["ut"][guvi_idx])]
    gx, gy = polar_xy(guvi["mlt"][guvi_idx], guvi["mlat"][guvi_idx])
    if len(gx) > 1:
        ax.plot(gx, gy, color="white", lw=4.0, alpha=0.78, zorder=13, solid_capstyle="round")
        ax.plot(gx, gy, color="0.05", lw=1.50, alpha=0.94, zorder=14, solid_capstyle="round")
    guvi_scatter = ax.scatter(
        gx,
        gy,
        c=guvi["on2"][guvi_idx],
        cmap="viridis",
        vmin=0.0,
        vmax=1.1,
        s=20,
        edgecolors="black",
        linewidths=0.16,
        zorder=15,
    )

    hemi_name = "North" if orbit.hemi == "N" else "South"
    ax.set_title(
        f"{hemi_name}: SSUSI {orbit.sat} LBHS REV {orbit.rev}\n"
        f"SSUSI UT {orbit.ut_min:.2f}-{orbit.ut_max:.2f}; DMSP drift and GUVI overlaid",
        fontsize=10.2,
        pad=8,
    )

    info = {
        "hemi": orbit.hemi,
        "sat": orbit.sat,
        "rev": orbit.rev,
        "file": orbit.path.name,
        "ssusi_ut_min": orbit.ut_min,
        "ssusi_ut_max": orbit.ut_max,
        "ssusi_pixels": int(np.count_nonzero(orbit.visible)),
        "dmsp_points": int(len(dm_idx)),
        "dmsp_ut_min": float(np.nanmin(dmsp["ut"][dm_idx])) if len(dm_idx) else np.nan,
        "dmsp_ut_max": float(np.nanmax(dmsp["ut"][dm_idx])) if len(dm_idx) else np.nan,
        "drift_p95_abs": float(np.nanpercentile(np.abs(drift_kms), 95)) if len(drift_kms) else np.nan,
        "drift_max_abs": float(np.nanmax(np.abs(drift_kms))) if len(drift_kms) else np.nan,
        "guvi_points": int(len(guvi_idx)),
        "guvi_ut_min": float(np.nanmin(guvi["ut"][guvi_idx])) if len(guvi_idx) else np.nan,
        "guvi_ut_max": float(np.nanmax(guvi["ut"][guvi_idx])) if len(guvi_idx) else np.nan,
        "guvi_on2_p05": float(np.nanpercentile(guvi["on2"][guvi_idx], 5)) if len(guvi_idx) else np.nan,
        "coastlines": coast,
        "score": orbit.score,
    }
    return ssusi_mesh, guvi_scatter, info


def choose_orbits(dmsp: dict[str, np.ndarray], guvi: dict[str, np.ndarray]) -> dict[str, SsusiOrbit]:
    candidates = {"N": [], "S": []}
    for path in sorted(DATA_DIR.glob("dmspf1[78]_ssusi_edr-aurora_*.nc")):
        for hemi in ["N", "S"]:
            orbit = read_ssusi(path, hemi, dmsp, guvi)
            if np.isfinite(orbit.score):
                candidates[hemi].append(orbit)

    if not candidates["N"] or not candidates["S"]:
        raise RuntimeError("No usable F17/F18 SSUSI files found for both hemispheres.")

    selected_n = max(candidates["N"], key=lambda item: item.score)

    # For the south we keep the storm/SAPS-like late-UT GUVI window if available;
    # otherwise fall back to the highest score.
    late_south = [
        item
        for item in candidates["S"]
        if item.sat == "F17" and 22.0 <= item.ut_min <= 22.8 and item.ut_max <= 23.1
    ]
    selected_s = max(late_south, key=lambda item: item.score) if late_south else max(candidates["S"], key=lambda item: item.score)
    return {"N": selected_n, "S": selected_s}


def make_figure(orbits: dict[str, SsusiOrbit], dmsp: dict[str, np.ndarray], guvi: dict[str, np.ndarray]) -> tuple[Path, list[dict[str, object]]]:
    ssusi_cmap = cmap_aurora_geospacelab()
    ssusi_cmap.set_bad((1, 1, 1, 0))

    fig, axes = plt.subplots(1, 2, figsize=(13.4, 7.35), dpi=220)
    fig.subplots_adjust(left=0.035, right=0.965, top=0.86, bottom=0.27, wspace=0.18)
    infos = []
    ssusi_mesh = guvi_scatter = None
    for ax, hemi in zip(axes, ["N", "S"]):
        ssusi_mesh, guvi_scatter, info = plot_panel(ax, orbits[hemi], dmsp, guvi, ssusi_cmap)
        infos.append(info)

    legend_handles = [
        Line2D([0], [0], color=DMSP_PURPLE, lw=1.35, label="DMSP SSIES track"),
        Line2D([0], [0], color=DMSP_PURPLE, lw=1.1, marker=r"$\rightarrow$", label="DMSP drift arrow length"),
        Line2D([0], [0], color="0.05", lw=1.65, label="GUVI track"),
    ]
    fig.legend(handles=legend_handles, loc="lower center", ncol=3, fontsize=8.0, frameon=False, bbox_to_anchor=(0.50, 0.035))

    cax1 = fig.add_axes([0.265, 0.165, 0.22, 0.018])
    cbar1 = fig.colorbar(ssusi_mesh, cax=cax1, orientation="horizontal", extend="max")
    cbar1.set_label("SSUSI LBHS (R)", fontsize=8.0)
    cbar1.ax.tick_params(labelsize=7.0)
    cbar1.ax.xaxis.set_label_position("top")

    cax2 = fig.add_axes([0.545, 0.165, 0.22, 0.018])
    cbar2 = fig.colorbar(guvi_scatter, cax=cax2, orientation="horizontal")
    cbar2.set_label("GUVI O/N2", fontsize=8.0)
    cbar2.ax.tick_params(labelsize=7.0)
    cbar2.ax.xaxis.set_label_position("top")

    fig.suptitle("17 Mar 2015 DMSP/SSUSI LBHS with DMSP SSIES Drift and TIMED/GUVI O/N2", fontsize=12.0, y=0.985)
    fig.text(
        0.5,
        0.110,
        "SSUSI MLAT/MLT are from the EDR-Aurora grid; DMSP/GUVI MLAT/MLT use the local centered-dipole screening transform.",
        ha="center",
        fontsize=7.6,
        color="0.36",
    )

    out = SCRIPT_DIR / "dmsp_ssusi_dmsp_velocity_arrows_guvi_global_style_best_NS_20150317.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out, infos


def make_single(orbit: SsusiOrbit, dmsp: dict[str, np.ndarray], guvi: dict[str, np.ndarray]) -> tuple[Path, dict[str, object]]:
    ssusi_cmap = cmap_aurora_geospacelab()
    ssusi_cmap.set_bad((1, 1, 1, 0))
    fig = plt.figure(figsize=(7.4, 7.8), dpi=220)
    ax = fig.add_axes([0.08, 0.29, 0.84, 0.61])
    ssusi_mesh, guvi_scatter, info = plot_panel(ax, orbit, dmsp, guvi, ssusi_cmap)

    cax1 = fig.add_axes([0.22, 0.170, 0.24, 0.020])
    cbar1 = fig.colorbar(ssusi_mesh, cax=cax1, orientation="horizontal", extend="max")
    cbar1.set_label("SSUSI LBHS (R)", fontsize=8.0)
    cbar1.ax.xaxis.set_label_position("top")
    cbar1.ax.tick_params(labelsize=7.0)
    cax2 = fig.add_axes([0.56, 0.170, 0.24, 0.020])
    cbar2 = fig.colorbar(guvi_scatter, cax=cax2, orientation="horizontal")
    cbar2.set_label("GUVI O/N2", fontsize=8.0)
    cbar2.ax.xaxis.set_label_position("top")
    cbar2.ax.tick_params(labelsize=7.0)

    fig.legend(
        handles=[
            Line2D([0], [0], color=DMSP_PURPLE, lw=1.35, label="DMSP SSIES track"),
            Line2D([0], [0], color=DMSP_PURPLE, lw=1.1, marker=r"$\rightarrow$", label="DMSP drift arrow length"),
            Line2D([0], [0], color="0.05", lw=1.5, label="GUVI track"),
        ],
        loc="lower center",
        ncol=3,
        fontsize=8.0,
        frameon=False,
        bbox_to_anchor=(0.50, 0.045),
    )

    suffix = "north" if orbit.hemi == "N" else "south"
    out = SCRIPT_DIR / f"dmsp_ssusi_dmsp_velocity_arrows_guvi_global_style_best_{suffix}_20150317.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out, info


def write_summary(path: Path, figure_path: Path, single_paths: list[Path], infos: list[dict[str, object]]) -> None:
    lines = [
        "DMSP/SSUSI + DMSP SSIES drift + TIMED/GUVI overlay, 17 Mar 2015",
        "",
        "Main figure:",
        f"- {figure_path.name}",
        "",
        "Single-panel figures:",
    ]
    for p in single_paths:
        lines.append(f"- {p.name}")
    lines.extend(
        [
            "",
        "Plot choices:",
        "- SSUSI background: EDR-Aurora LBHS, GeospaceLAB default aurora colormap, log scale 10-6000 R.",
        "- DMSP track: same satellite as SSUSI, drawn in purple following the style in DMSP_vi.m.",
        "- DMSP drift: SSIES horizontal ion drift is projected into arrows approximately perpendicular to the track; arrow length scales with km/s.",
        "- GUVI overlay: TIMED/GUVI O/N2 track in the same hemisphere and near the SSUSI valid-UT window.",
        "- GUVI color: viridis with limits 0-1.1, matching the earlier GUVI global map style.",
            "",
            "Selected panels:",
        ]
    )
    for info in infos:
        hemi_name = "North" if info["hemi"] == "N" else "South"
        lines.extend(
            [
                f"- {hemi_name}: {info['sat']} REV {info['rev']}, file={info['file']}",
                f"  SSUSI valid UT {info['ssusi_ut_min']:.2f}-{info['ssusi_ut_max']:.2f}; pixels={info['ssusi_pixels']}; score={info['score']:.1f}",
                f"  DMSP points={info['dmsp_points']}, UT {info['dmsp_ut_min']:.2f}-{info['dmsp_ut_max']:.2f}, |drift| p95/max={info['drift_p95_abs']:.2f}/{info['drift_max_abs']:.2f} km/s",
                f"  GUVI points={info['guvi_points']}, UT {info['guvi_ut_min']:.2f}-{info['guvi_ut_max']:.2f}, O/N2 p05={info['guvi_on2_p05']:.3f}",
                f"  Coastlines added={info['coastlines']}",
            ]
        )
    lines.extend(
        [
            "",
            "Caveat:",
            "- SSUSI MLAT/MLT are product-grid coordinates; DMSP/GUVI MLAT/MLT use the local centered-dipole transform rather than AACGMV2.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    dmsp = read_dmsp()
    guvi = read_guvi_raw_cd(GUVI_FILE)
    orbits = choose_orbits(dmsp, guvi)
    combined, infos = make_figure(orbits, dmsp, guvi)
    single_paths = []
    single_infos = []
    for hemi in ["N", "S"]:
        path, info = make_single(orbits[hemi], dmsp, guvi)
        single_paths.append(path)
        single_infos.append(info)
    summary = SCRIPT_DIR / "dmsp_ssusi_dmsp_velocity_arrows_guvi_global_style_best_NS_20150317_summary.txt"
    write_summary(summary, combined, single_paths, infos)
    print(f"Saved {combined}")
    for path in single_paths:
        print(f"Saved {path}")
    print(f"Saved {summary}")


if __name__ == "__main__":
    main()

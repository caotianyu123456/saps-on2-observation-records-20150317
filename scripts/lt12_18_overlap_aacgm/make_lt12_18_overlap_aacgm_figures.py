from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import aacgmv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.lines import Line2D
from netCDF4 import Dataset
import numpy as np
import pandas as pd
from PIL import Image


SCRIPT_DIR = Path(__file__).resolve().parent
CHAT_DIR = SCRIPT_DIR.parent
WORKSPACE = CHAT_DIR.parent

GUVI_FILE = WORKSPACE / "timed_guvi_l3-on2_2015076_Av0100r000.nc"
DMSP_FILES = [
    WORKSPACE / "dmsp_f17_ssies_20150317_parsed.csv",
    WORKSPACE / "dmsp_f18_ssies_20150317_parsed.csv",
]
SSUSI_DATA_DIR = CHAT_DIR / "dmsp_ssusi_guvi_overlay" / "data"
SUPERDARN_IMAGE = CHAT_DIR / "convection_maps_s_20150317_215800.png"

EVENT_DATE = datetime(2015, 3, 17)
AACGM_DATE = datetime(2015, 3, 17, 12)
HEMI = "S"
MLT_RANGE = (12.0, 18.0)
LAT_ABS_RANGE = (45.0, 80.0)
SUPERDARN_FILE_UT = 21.0 + 58.0 / 60.0
SUPERDARN_FIRST_PANEL_START = SUPERDARN_FILE_UT - 8.0 / 60.0
SUPERDARN_PANEL_CENTERS = [
    (392.0, 397.0),
    (1208.0, 397.0),
    (392.0, 1165.0),
    (1208.0, 1165.0),
    (800.0, 1934.0),
]
SUPERDARN_PANELS = [
    {
        "center": center,
        "radius": 277.0,
        "window": (
            SUPERDARN_FIRST_PANEL_START + i * 2.0 / 60.0,
            SUPERDARN_FIRST_PANEL_START + (i + 1) * 2.0 / 60.0,
        ),
    }
    for i, center in enumerate(SUPERDARN_PANEL_CENTERS)
]
SUPERDARN_SELECTED_PANEL = SUPERDARN_PANELS[-1]


@dataclass
class SsusiOrbit:
    path: Path
    sat: str
    rev: str
    hemi: str
    start: datetime
    stop: datetime
    mlat: np.ndarray
    mlt: np.ndarray
    ut: np.ndarray
    lbhs: np.ndarray
    visible: np.ndarray
    score: float = -np.inf

    @property
    def ut_min(self) -> float:
        return float(np.nanmin(self.ut[self.visible]))

    @property
    def ut_max(self) -> float:
        return float(np.nanmax(self.ut[self.visible]))


def fractional_doy_to_time(doy: np.ndarray) -> pd.DatetimeIndex:
    return pd.Timestamp(EVENT_DATE.year, 1, 1) + pd.to_timedelta(doy - 1.0, unit="D")


def ut_from_time(times: pd.DatetimeIndex | pd.Series) -> np.ndarray:
    t = pd.to_datetime(times)
    return (
        t.hour.to_numpy(dtype=float)
        + t.minute.to_numpy(dtype=float) / 60.0
        + t.second.to_numpy(dtype=float) / 3600.0
        + t.microsecond.to_numpy(dtype=float) / 3.6e9
    )


def compute_mlt_by_minute(mlon: np.ndarray, times: pd.DatetimeIndex | pd.Series) -> np.ndarray:
    times = pd.Series(pd.to_datetime(times))
    minute = times.dt.floor("min")
    mlt = np.full(len(mlon), np.nan, dtype=float)
    index_series = pd.Series(np.arange(len(mlon)), index=minute)
    for minute_time, group in index_series.groupby(level=0):
        idx = group.to_numpy(dtype=int)
        if idx.size == 0:
            continue
        mlt[idx] = np.asarray(aacgmv2.convert_mlt(mlon[idx], minute_time.to_pydatetime()), dtype=float)
    return mlt


def read_guvi_aacgm() -> dict[str, np.ndarray]:
    with Dataset(GUVI_FILE) as ds:
        glat = np.asarray(ds.variables["LATITUDE"][:], dtype=float)
        glon = np.asarray(ds.variables["LONGITUDE"][:], dtype=float)
        on2 = np.asarray(ds.variables["ON2"][:], dtype=float)
        doy = np.asarray(ds.variables["FRACTIONAL_DOY"][:], dtype=float)
        orbit = np.asarray(ds.variables["ORBIT"][:], dtype=float)

    valid = (
        np.isfinite(glat)
        & np.isfinite(glon)
        & np.isfinite(on2)
        & (np.abs(on2) < 1e20)
        & np.isfinite(doy)
    )
    glat = glat[valid]
    glon = ((glon[valid] + 180.0) % 360.0) - 180.0
    on2 = on2[valid]
    doy = doy[valid]
    orbit = orbit[valid]
    times = fractional_doy_to_time(doy)

    mlat, mlon, _ = aacgmv2.convert_latlon_arr(
        glat,
        glon,
        np.full(glat.shape, 300.0),
        AACGM_DATE,
        method_code="G2A",
    )
    mlat = np.asarray(mlat, dtype=float)
    mlon = np.asarray(mlon, dtype=float)
    mlt = compute_mlt_by_minute(mlon, times)
    return {
        "time": times,
        "ut": ut_from_time(times),
        "glat": glat,
        "glon": glon,
        "mlat": mlat,
        "mlon": mlon,
        "mlt": mlt,
        "on2": on2,
        "orbit": orbit,
    }


def read_dmsp_aacgm() -> dict[str, np.ndarray]:
    frames = []
    for path in DMSP_FILES:
        frame = pd.read_csv(path, parse_dates=["time_iso"])
        frame["time"] = pd.to_datetime(frame["time_iso"])
        frames.append(frame)
    df = pd.concat(frames, ignore_index=True)
    glat = df["glat"].to_numpy(dtype=float)
    glon = ((df["glon"].to_numpy(dtype=float) + 180.0) % 360.0) - 180.0
    alt = df["alt_km"].to_numpy(dtype=float)
    times = pd.DatetimeIndex(df["time"])

    mlat, mlon, _ = aacgmv2.convert_latlon_arr(glat, glon, alt, AACGM_DATE, method_code="G2A")
    mlat = np.asarray(mlat, dtype=float)
    mlon = np.asarray(mlon, dtype=float)
    mlt = compute_mlt_by_minute(mlon, times)
    return {
        "satellite": df["satellite"].to_numpy(dtype=str),
        "time": times,
        "ut": ut_from_time(times),
        "glat": glat,
        "glon": glon,
        "alt_km": alt,
        "mlat": mlat,
        "mlon": mlon,
        "mlt": mlt,
        "horizontal_ion_drift_mps": df["horizontal_ion_drift_mps"].to_numpy(dtype=float),
    }


def in_window(ut: np.ndarray, start: float, end: float) -> np.ndarray:
    if start < 0:
        return (ut >= start + 24.0) | (ut <= end)
    if end >= 24.0:
        return (ut >= start) | (ut <= end - 24.0)
    return (ut >= start) & (ut <= end)


def in_hemi_sector(mlat: np.ndarray, mlt: np.ndarray, hemi: str = HEMI) -> np.ndarray:
    if hemi == "S":
        lat_mask = (mlat <= -LAT_ABS_RANGE[0]) & (mlat >= -LAT_ABS_RANGE[1])
    else:
        lat_mask = (mlat >= LAT_ABS_RANGE[0]) & (mlat <= LAT_ABS_RANGE[1])
    return lat_mask & (mlt >= MLT_RANGE[0]) & (mlt <= MLT_RANGE[1])


def scan_overlap_windows(guvi: dict[str, np.ndarray], dmsp: dict[str, np.ndarray]) -> pd.DataFrame:
    rows = []
    guvi_sector = in_hemi_sector(guvi["mlat"], guvi["mlt"], HEMI)
    dmsp_sector = in_hemi_sector(dmsp["mlat"], dmsp["mlt"], HEMI)
    westward = dmsp["horizontal_ion_drift_mps"] > 0.0
    for center in np.arange(0.0, 24.0, 0.25):
        start = center - 2.0
        end = center + 2.0
        gm = guvi_sector & in_window(guvi["ut"], start, end)
        dm = dmsp_sector & westward & in_window(dmsp["ut"], start, end)
        if np.count_nonzero(gm) < 50 or np.count_nonzero(dm) < 50:
            continue
        west = dmsp["horizontal_ion_drift_mps"][dm] / 1000.0
        rows.append(
            {
                "center_ut": center,
                "start_ut": start % 24.0,
                "end_ut": end % 24.0,
                "guvi_n": int(np.count_nonzero(gm)),
                "guvi_on2_median": float(np.nanmedian(guvi["on2"][gm])),
                "guvi_on2_min": float(np.nanmin(guvi["on2"][gm])),
                "dmsp_westward_n": int(np.count_nonzero(dm)),
                "dmsp_westward_median_kms": float(np.nanmedian(west)),
                "dmsp_westward_p95_kms": float(np.nanpercentile(west, 95)),
                "dmsp_westward_max_kms": float(np.nanmax(west)),
            }
        )
    candidates = pd.DataFrame(rows)
    if candidates.empty:
        return candidates
    candidates["score"] = (
        (1.1 - candidates["guvi_on2_median"]).clip(lower=0.0)
        * (0.55 * candidates["dmsp_westward_p95_kms"] + 0.45 * candidates["dmsp_westward_max_kms"])
        * np.log10(candidates["guvi_n"] + 10)
    )
    return candidates.sort_values("score", ascending=False).reset_index(drop=True)


def read_ssusi(path: Path, hemi: str = HEMI) -> SsusiOrbit:
    match = re.search(r"dmsp(?P<sat>f\d+)_ssusi_edr-aurora_.*-REV(?P<rev>\d+)_", path.name)
    if match is None:
        raise ValueError(f"Cannot parse SSUSI file name: {path.name}")
    sat = match.group("sat").upper()
    pole = "SOUTH" if hemi == "S" else "NORTH"
    suffix = "S" if hemi == "S" else "N"

    with Dataset(path) as ds:
        start = datetime.strptime(ds.STARTING_TIME, "%Y%j%H%M%S")
        stop = datetime.strptime(ds.STOPPING_TIME, "%Y%j%H%M%S")
        base_mlat = np.asarray(ds.variables["LATITUDE_GEOMAGNETIC_GRID_MAP"][:], dtype=float)
        mlat = -np.abs(base_mlat) if hemi == "S" else np.abs(base_mlat)
        mlt = np.asarray(ds.variables["MLT_GRID_MAP"][:], dtype=float)
        ut = np.asarray(ds.variables[f"UT_{suffix}"][:], dtype=float)
        lbhs = np.asarray(ds.variables[f"DISK_RADIANCEDATA_INTENSITY_{pole}"][3, :, :], dtype=float)

    invalid = (ut <= 0.0) | ~np.isfinite(lbhs) | (lbhs <= 0.0)
    lbhs = lbhs.copy()
    lbhs[invalid] = np.nan
    visible = np.isfinite(lbhs) & in_hemi_sector(mlat, mlt, hemi)
    return SsusiOrbit(
        path=path,
        sat=sat,
        rev=match.group("rev"),
        hemi=hemi,
        start=start,
        stop=stop,
        mlat=mlat,
        mlt=mlt,
        ut=ut,
        lbhs=lbhs,
        visible=visible,
    )


def score_ssusi_orbit(
    orbit: SsusiOrbit,
    guvi: dict[str, np.ndarray],
    dmsp: dict[str, np.ndarray],
) -> SsusiOrbit:
    if not np.any(orbit.visible):
        orbit.score = -np.inf
        return orbit
    u0 = orbit.ut_min
    u1 = orbit.ut_max
    gm = in_hemi_sector(guvi["mlat"], guvi["mlt"], HEMI) & in_window(guvi["ut"], u0 - 2.0, u1 + 2.0)
    dm = (
        (dmsp["satellite"] == orbit.sat)
        & in_hemi_sector(dmsp["mlat"], dmsp["mlt"], HEMI)
        & in_window(dmsp["ut"], u0 - 2.0, u1 + 2.0)
    )
    if np.count_nonzero(dm) < 50:
        orbit.score = -np.inf
        return orbit
    drift = np.abs(dmsp["horizontal_ion_drift_mps"][dm]) / 1000.0
    drift_p95 = float(np.nanpercentile(drift, 95)) if drift.size else 0.0
    orbit.score = (
        min(int(np.count_nonzero(orbit.visible)), 22000) * 0.006
        + min(int(np.count_nonzero(gm)), 450) * 0.55
        + min(int(np.count_nonzero(dm)), 1800) * 0.22
        + drift_p95 * 90.0
    )
    return orbit


def select_ssusi_orbit(guvi: dict[str, np.ndarray], dmsp: dict[str, np.ndarray]) -> SsusiOrbit:
    paths = sorted(SSUSI_DATA_DIR.glob("dmspf*_ssusi_edr-aurora_2015076T*-REV*_v*.nc"))
    if not paths:
        raise FileNotFoundError(f"No SSUSI files found in {SSUSI_DATA_DIR}")
    orbits = [score_ssusi_orbit(read_ssusi(path, HEMI), guvi, dmsp) for path in paths]
    return sorted(orbits, key=lambda item: item.score, reverse=True)[0]


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


def polar_xy(mlt: np.ndarray, mlat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    radius = 90.0 - np.abs(mlat)
    theta = np.pi / 2.0 + ((mlt - 12.0) / 24.0) * 2.0 * np.pi
    return radius * np.cos(theta), radius * np.sin(theta)


def split_xy(x: np.ndarray, y: np.ndarray, max_jump: float = 12.0) -> list[tuple[np.ndarray, np.ndarray]]:
    valid = np.isfinite(x) & np.isfinite(y)
    idx = np.where(valid)[0]
    if idx.size == 0:
        return []
    vx = x[idx]
    vy = y[idx]
    groups = []
    start = 0
    for i in range(1, idx.size):
        if idx[i] != idx[i - 1] + 1 or np.hypot(vx[i] - vx[i - 1], vy[i] - vy[i - 1]) > max_jump:
            groups.append((vx[start:i], vy[start:i]))
            start = i
    groups.append((vx[start:], vy[start:]))
    return groups


def mlat_mlt_to_superdarn_pixels(
    mlat: np.ndarray,
    mlt: np.ndarray,
    center: tuple[float, float],
    radius: float,
) -> tuple[np.ndarray, np.ndarray]:
    rho = (90.0 - np.abs(np.asarray(mlat, dtype=float))) / 40.0 * radius
    theta = 2.0 * np.pi * (np.asarray(mlt, dtype=float) - 6.0) / 24.0
    return center[0] + rho * np.cos(theta), center[1] - rho * np.sin(theta)


def draw_sector_on_superdarn(ax: plt.Axes, panel: dict[str, object]) -> None:
    center = panel["center"]
    radius = panel["radius"]
    lat_abs = np.linspace(LAT_ABS_RANGE[0], LAT_ABS_RANGE[1], 80)
    for mlt in MLT_RANGE:
        x, y = mlat_mlt_to_superdarn_pixels(-lat_abs, np.full_like(lat_abs, mlt), center, radius)
        ax.plot(x, y, color="#ffd34d", lw=1.45, alpha=0.96, zorder=18)
    for lat in LAT_ABS_RANGE:
        mlt = np.linspace(MLT_RANGE[0], MLT_RANGE[1], 120)
        x, y = mlat_mlt_to_superdarn_pixels(np.full_like(mlt, -lat), mlt, center, radius)
        ax.plot(x, y, color="#ffd34d", lw=1.10, alpha=0.90, zorder=18)


def draw_polar_grid(ax: plt.Axes) -> None:
    radius_limit = 90.0 - LAT_ABS_RANGE[0]
    phi = np.linspace(0, 2 * np.pi, 500)
    ax.add_patch(plt.Circle((0.0, 0.0), radius_limit, facecolor="#fbf8f0", edgecolor="none", zorder=0))
    for lat in [50, 60, 70, 80]:
        r = 90.0 - lat
        ax.plot(r * np.cos(phi), r * np.sin(phi), color="#58351e", lw=0.55, ls=":", alpha=0.72, zorder=1)
        ax.text(0.45, r + 0.7, f"{lat}S", fontsize=7.2, color="0.34", ha="left", va="bottom")
    ax.plot(radius_limit * np.cos(phi), radius_limit * np.sin(phi), color="black", lw=0.85, zorder=2)
    for mlt in range(0, 24, 3):
        theta = np.pi / 2.0 + ((mlt - 12.0) / 24.0) * 2.0 * np.pi
        ax.plot(
            [0.0, radius_limit * np.cos(theta)],
            [0.0, radius_limit * np.sin(theta)],
            color="#58351e",
            lw=0.45,
            ls=":",
            alpha=0.68,
            zorder=1,
        )
    for mlt, label in [(12, "12"), (6, "06"), (0, "00"), (18, "18")]:
        theta = np.pi / 2.0 + ((mlt - 12.0) / 24.0) * 2.0 * np.pi
        ax.text(
            (radius_limit + 3.3) * np.cos(theta),
            (radius_limit + 3.3) * np.sin(theta),
            label,
            ha="center",
            va="center",
            fontsize=8.8,
            color="0.2",
        )
    ax.set_aspect("equal")
    ax.set_xlim(-radius_limit - 8, radius_limit + 8)
    ax.set_ylim(-radius_limit - 8, radius_limit + 8)
    ax.axis("off")


def draw_sector_on_polar(ax: plt.Axes) -> None:
    mlt = np.linspace(MLT_RANGE[0], MLT_RANGE[1], 140)
    for lat_abs in LAT_ABS_RANGE:
        x, y = polar_xy(mlt, -np.full_like(mlt, lat_abs))
        ax.plot(x, y, color="#e0a800", lw=1.2, zorder=5)
    lat_abs = np.linspace(LAT_ABS_RANGE[0], LAT_ABS_RANGE[1], 100)
    for mlt0 in MLT_RANGE:
        x, y = polar_xy(np.full_like(lat_abs, mlt0), -lat_abs)
        ax.plot(x, y, color="#e0a800", lw=1.35, zorder=5)
    x1, y1 = polar_xy(np.full_like(lat_abs, MLT_RANGE[0]), -lat_abs)
    x2, y2 = polar_xy(np.full_like(lat_abs, MLT_RANGE[1]), -lat_abs)
    ax.fill(
        np.r_[x1, x2[::-1]],
        np.r_[y1, y2[::-1]],
        color="#ffd34d",
        alpha=0.10,
        zorder=4,
        ec="none",
    )


def overlay_aacgm_coastlines(ax: plt.Axes, target_time: datetime) -> bool:
    try:
        import cartopy
        import cartopy.io.shapereader as shpreader
    except Exception:
        return False
    cartopy.config["data_dir"] = str(CHAT_DIR / "dmsp_ssusi_guvi_overlay" / "cartopy_data")
    try:
        land_path = shpreader.natural_earth(resolution="110m", category="physical", name="land")
        reader = shpreader.Reader(land_path)
    except Exception:
        return False

    for geom in reader.geometries():
        polygons = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
        for polygon in polygons:
            lon = np.asarray(polygon.exterior.coords.xy[0], dtype=float)
            lat = np.asarray(polygon.exterior.coords.xy[1], dtype=float)
            if lon.size < 3:
                continue
            mlat, mlon, _ = aacgmv2.convert_latlon_arr(lat, lon, np.full_like(lat, 300.0), target_time, "G2A")
            mlat = np.asarray(mlat, dtype=float)
            mlon = np.asarray(mlon, dtype=float)
            mlt = np.asarray(aacgmv2.convert_mlt(mlon, target_time), dtype=float)
            ok = (mlat <= -LAT_ABS_RANGE[0]) & (mlat >= -LAT_ABS_RANGE[1]) & np.isfinite(mlt)
            x, y = polar_xy(mlt, mlat)
            x = np.where(ok, x, np.nan)
            y = np.where(ok, y, np.nan)
            for sx, sy in split_xy(x, y, max_jump=10.0):
                if sx.size >= 2:
                    ax.plot(sx, sy, color="0.55", lw=0.42, alpha=0.72, zorder=3)
    return True


def draw_drift_arrows_display(
    ax: plt.Axes,
    x: np.ndarray,
    y: np.ndarray,
    drift_kms: np.ndarray,
    step: int,
    color: str,
    pixels_per_kms: float,
    zorder: int,
) -> None:
    if len(x) < 5:
        return
    xy_disp = ax.transData.transform(np.column_stack([x, y]))
    tangent = np.gradient(xy_disp, axis=0)
    norm = np.hypot(tangent[:, 0], tangent[:, 1])
    ok = norm > 0
    tangent[ok] /= norm[ok, None]
    normal = np.column_stack([-tangent[:, 1], tangent[:, 0]])
    positions = np.arange(4, len(x) - 4, max(step, 1))
    if len(positions) > 34:
        positions = positions[np.linspace(0, len(positions) - 1, 34, dtype=int)]
    for pos in positions:
        speed = drift_kms[pos]
        if not np.isfinite(speed):
            continue
        length_px = min(abs(speed), 5.0) * pixels_per_kms
        if length_px < 2.5:
            continue
        sign = 1.0 if speed >= 0.0 else -1.0
        start = ax.transData.transform((x[pos], y[pos]))
        end = start + normal[pos] * length_px * sign
        end_xy = ax.transData.inverted().transform(end)
        ax.annotate(
            "",
            xy=end_xy,
            xytext=(x[pos], y[pos]),
            arrowprops=dict(
                arrowstyle="-|>",
                color=color,
                lw=0.75,
                mutation_scale=5.4,
                shrinkA=0,
                shrinkB=0,
            ),
            zorder=zorder,
        )


def split_sorted_track(mask: np.ndarray, time: pd.DatetimeIndex, x: np.ndarray, y: np.ndarray, max_jump: float) -> list[np.ndarray]:
    idx = np.where(mask)[0]
    if idx.size == 0:
        return []
    idx = idx[np.argsort(time[idx])]
    groups = []
    start = 0
    for i in range(1, idx.size):
        if np.hypot(x[idx[i]] - x[idx[i - 1]], y[idx[i]] - y[idx[i - 1]]) > max_jump:
            groups.append(idx[start:i])
            start = i
    groups.append(idx[start:])
    return [g for g in groups if g.size >= 2]


def plot_superdarn(
    guvi: dict[str, np.ndarray],
    dmsp: dict[str, np.ndarray],
    orbit: SsusiOrbit,
) -> tuple[Path, dict[str, object]]:
    if not SUPERDARN_IMAGE.exists():
        raise FileNotFoundError(f"Missing SuperDARN image: {SUPERDARN_IMAGE}")
    full_image = np.asarray(Image.open(SUPERDARN_IMAGE).convert("RGB"))
    full_height, full_width = full_image.shape[:2]
    panel = dict(SUPERDARN_SELECTED_PANEL)
    cx, cy = panel["center"]
    radius = panel["radius"]
    x0 = max(0, int(cx - radius - 150))
    x1 = min(full_width, int(cx + radius + 330))
    y0 = max(0, int(cy - radius - 145))
    y1 = min(full_height, int(cy + radius + 145))
    image = full_image[y0:y1, x0:x1, :]
    panel["center"] = (cx - x0, cy - y0)
    height, width = image.shape[:2]
    fig, ax = plt.subplots(figsize=(width / 185.0, height / 185.0), dpi=210)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.24)
    ax.imshow(image, extent=(0, width, height, 0))
    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)
    ax.axis("off")

    u0 = orbit.ut_min - 2.0
    u1 = orbit.ut_max + 2.0
    draw_sector_on_superdarn(ax, panel)
    guvi_all = in_hemi_sector(guvi["mlat"], guvi["mlt"], HEMI) & in_window(guvi["ut"], u0, u1)
    dmsp_all = in_hemi_sector(dmsp["mlat"], dmsp["mlt"], HEMI) & in_window(dmsp["ut"], u0, u1)
    guvi_scatter = None
    colors = {"F17": "#7a1688", "F18": "#2455a4"}

    if np.any(guvi_all):
        idx = np.where(guvi_all)[0]
        idx = idx[np.argsort(guvi["ut"][idx])]
        x, y = mlat_mlt_to_superdarn_pixels(
            guvi["mlat"][idx],
            guvi["mlt"][idx],
            panel["center"],
            panel["radius"],
        )
        for sx, sy in split_xy(x, y, max_jump=65.0):
            ax.plot(
                sx,
                sy,
                color="white",
                lw=3.2,
                alpha=0.96,
                zorder=20,
                solid_capstyle="round",
                path_effects=[pe.Stroke(linewidth=5.0, foreground="black", alpha=0.56), pe.Normal()],
            )
        guvi_scatter = ax.scatter(
            x,
            y,
            c=guvi["on2"][idx],
            cmap="viridis",
            vmin=0.0,
            vmax=1.1,
            s=25,
            edgecolor="black",
            linewidth=0.45,
            zorder=23,
        )

    for sat, color in colors.items():
        sat_mask = dmsp_all & (dmsp["satellite"] == sat)
        if not np.any(sat_mask):
            continue
        idx = np.where(sat_mask)[0]
        idx = idx[np.argsort(dmsp["ut"][idx])]
        x, y = mlat_mlt_to_superdarn_pixels(
            dmsp["mlat"][idx],
            dmsp["mlt"][idx],
            panel["center"],
            panel["radius"],
        )
        for group in split_sorted_track(np.ones_like(idx, dtype=bool), dmsp["time"][idx], x, y, 60.0):
            gx = x[group]
            gy = y[group]
            ax.plot(gx, gy, color=color, lw=1.75, alpha=0.92, zorder=24)
            draw_drift_arrows_display(
                ax,
                gx,
                gy,
                dmsp["horizontal_ion_drift_mps"][idx[group]] / 1000.0,
                step=max(12, len(group) // 18),
                color=color,
                pixels_per_kms=34.0,
                zorder=25,
            )

    if guvi_scatter is not None:
        cax = fig.add_axes([0.30, 0.055, 0.42, 0.022])
        cbar = fig.colorbar(guvi_scatter, cax=cax, orientation="horizontal")
        cbar.set_label("TIMED/GUVI O/N2", fontsize=8)
        cbar.ax.tick_params(labelsize=7)

    fig.text(
        0.03,
        0.165,
        "AACGM overlay: 12-18 MLT sector; GUVI O/N2 + DMSP SSIES drift arrows",
        color="black",
        fontsize=10.8,
        weight="bold",
        ha="left",
        va="bottom",
    )
    fig.text(
        0.03,
        0.133,
        (
            "SuperDARN selected panel: southern hemisphere, 2015-03-17 21:58-22:00 UT; "
            f"tracks shown for {u0:.2f}-{u1:.2f} UT (SSUSI +/-2 h)"
        ),
        color="black",
        fontsize=7.9,
        ha="left",
        va="bottom",
    )
    handles = [
        Line2D([0], [0], color="#7a1688", lw=2.2, label="DMSP F17"),
        Line2D([0], [0], color="#2455a4", lw=2.2, label="DMSP F18"),
        Line2D([0], [0], color="black", lw=2.4, label="GUVI track"),
        Line2D([0], [0], color="#ffd34d", lw=1.8, label="12-18 MLT sector"),
    ]
    leg = ax.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.985, 0.985), frameon=True, fontsize=7.3)
    leg.get_frame().set_facecolor("white")
    leg.get_frame().set_alpha(0.78)

    out = SCRIPT_DIR / "superdarn_aacgm_guvi_dmsp_tracks_20150317_south_2158_panel_pm2h.png"
    fig.savefig(out, facecolor="white", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)

    info = {
        "track_window": (u0, u1),
        "panel_window": panel["window"],
        "guvi_counts": [int(np.count_nonzero(guvi_all))],
        "dmsp_counts": [int(np.count_nonzero(dmsp_all))],
        "guvi_mask": guvi_all,
        "dmsp_mask": dmsp_all,
    }
    return out, info


def plot_ssusi(
    orbit: SsusiOrbit,
    guvi: dict[str, np.ndarray],
    dmsp: dict[str, np.ndarray],
) -> tuple[Path, dict[str, object]]:
    u0 = orbit.ut_min
    u1 = orbit.ut_max
    target_time = EVENT_DATE + timedelta(hours=(u0 + u1) / 2.0)
    guvi_mask = in_hemi_sector(guvi["mlat"], guvi["mlt"], HEMI) & in_window(guvi["ut"], u0 - 2.0, u1 + 2.0)
    dmsp_mask = (
        (dmsp["satellite"] == orbit.sat)
        & in_hemi_sector(dmsp["mlat"], dmsp["mlt"], HEMI)
        & in_window(dmsp["ut"], u0 - 2.0, u1 + 2.0)
    )

    fig, ax = plt.subplots(figsize=(8.4, 8.35), dpi=240)
    fig.subplots_adjust(left=0.045, right=0.86, top=0.84, bottom=0.075)
    fig.text(
        0.045,
        0.965,
        f"DMSP-{orbit.sat[-2:]} SSUSI LBHS + DMSP SSIES + TIMED/GUVI",
        ha="left",
        va="top",
        fontsize=13.0,
        weight="bold",
    )
    fig.text(
        0.045,
        0.928,
        f"South, 2015-03-17; SSUSI REV {orbit.rev}, valid UT {u0:.2f}-{u1:.2f}; 12-18 MLT overlap window",
        ha="left",
        va="top",
        fontsize=8.9,
        color="0.30",
    )
    draw_polar_grid(ax)
    coast_ok = overlay_aacgm_coastlines(ax, target_time)
    draw_sector_on_polar(ax)

    x, y = polar_xy(orbit.mlt, orbit.mlat)
    lbhs = np.where(np.isfinite(orbit.lbhs), orbit.lbhs, np.nan)
    mesh = ax.pcolormesh(
        x,
        y,
        lbhs,
        cmap=cmap_aurora_geospacelab(),
        norm=LogNorm(vmin=10.0, vmax=6000.0),
        shading="auto",
        zorder=6,
    )

    if np.any(guvi_mask):
        gx, gy = polar_xy(guvi["mlt"][guvi_mask], guvi["mlat"][guvi_mask])
        guvi_scatter = ax.scatter(
            gx,
            gy,
            c=guvi["on2"][guvi_mask],
            cmap="viridis",
            vmin=0.0,
            vmax=1.1,
            s=8.5,
            edgecolor="none",
            linewidth=0.0,
            alpha=0.92,
            zorder=12,
            label="TIMED/GUVI O/N2",
        )
    else:
        guvi_scatter = None

    if np.any(dmsp_mask):
        idx = np.where(dmsp_mask)[0]
        idx = idx[np.argsort(dmsp["ut"][idx])]
        dx, dy = polar_xy(dmsp["mlt"][idx], dmsp["mlat"][idx])
        for sx, sy in split_xy(dx, dy, max_jump=12.0):
            ax.plot(sx, sy, color="#7a1688", lw=2.25, alpha=0.96, zorder=14)
        draw_drift_arrows_display(
            ax,
            dx,
            dy,
            dmsp["horizontal_ion_drift_mps"][idx] / 1000.0,
            step=max(18, idx.size // 30),
            color="#7a1688",
            pixels_per_kms=21.0,
            zorder=15,
        )

    cax1 = fig.add_axes([0.875, 0.29, 0.018, 0.42])
    cbar1 = fig.colorbar(mesh, cax=cax1)
    cbar1.set_label("SSUSI LBHS (R)", fontsize=8.2)
    cbar1.ax.tick_params(labelsize=7.2)
    if guvi_scatter is not None:
        cax2 = fig.add_axes([0.12, 0.052, 0.36, 0.018])
        cbar2 = fig.colorbar(guvi_scatter, cax=cax2, orientation="horizontal")
        cbar2.set_label("GUVI O/N2", fontsize=8.2)
        cbar2.ax.tick_params(labelsize=7.2)

    ax.text(
        0.02,
        0.055,
        "Purple arrows: DMSP horizontal ion drift; arrow length scales with speed",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8.1,
        color="#5b1267",
        bbox=dict(fc="white", ec="none", alpha=0.68, pad=1.5),
        zorder=30,
    )
    handles = [
        Line2D([0], [0], color="#7a1688", lw=2.3, label=f"DMSP {orbit.sat} track + drift"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#35b779", markeredgecolor="black", markersize=6, label="GUVI O/N2 samples"),
        Line2D([0], [0], color="#e0a800", lw=1.5, label="12-18 MLT sector"),
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=8.0, frameon=True)
    if coast_ok:
        ax.text(0.985, 0.02, "Coastlines in AACGM/MLT", transform=ax.transAxes, ha="right", va="bottom", fontsize=6.8, color="0.36")

    out = SCRIPT_DIR / f"dmsp_ssusi_aacgm_guvi_dmsp_velocity_20150317_south_{orbit.sat.lower()}_rev{orbit.rev}.png"
    fig.savefig(out, facecolor="white", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)

    info = {
        "guvi_mask": guvi_mask,
        "dmsp_mask": dmsp_mask,
        "coastlines": coast_ok,
    }
    return out, info


def describe_mask(prefix: str, data: dict[str, np.ndarray], mask: np.ndarray, value_key: str | None = None) -> list[str]:
    if not np.any(mask):
        return [f"- {prefix}: n=0"]
    lines = [
        (
            f"- {prefix}: n={int(np.count_nonzero(mask))}, "
            f"UT={np.nanmin(data['ut'][mask]):.3f}-{np.nanmax(data['ut'][mask]):.3f}, "
            f"AACGM MLAT={np.nanmin(data['mlat'][mask]):.1f}..{np.nanmax(data['mlat'][mask]):.1f}, "
            f"MLT={np.nanmin(data['mlt'][mask]):.2f}..{np.nanmax(data['mlt'][mask]):.2f}"
        )
    ]
    if value_key is not None:
        values = np.asarray(data[value_key][mask], dtype=float)
        if value_key == "horizontal_ion_drift_mps":
            values = values / 1000.0
            lines.append(
                f"  drift km/s: median={np.nanmedian(values):.2f}, |p95|={np.nanpercentile(np.abs(values), 95):.2f}, |max|={np.nanmax(np.abs(values)):.2f}"
            )
        else:
            lines.append(
                f"  {value_key}: median={np.nanmedian(values):.3f}, p05={np.nanpercentile(values, 5):.3f}, min={np.nanmin(values):.3f}"
            )
    return lines


def write_summary(
    candidates: pd.DataFrame,
    orbit: SsusiOrbit,
    superdarn_out: Path,
    superdarn_info: dict[str, object],
    ssusi_out: Path,
    ssusi_info: dict[str, object],
    guvi: dict[str, np.ndarray],
    dmsp: dict[str, np.ndarray],
) -> Path:
    out = SCRIPT_DIR / "lt12_18_overlap_aacgm_summary.txt"
    lines = [
        "AACGM 12-18 MLT overlap screening for 2015-03-17",
        "",
        "Goal:",
        "- Focus on GUVI daytime-side coverage that overlaps SAPS-relevant dusk sector, especially 12-18 MLT.",
        "- Overlay GUVI and DMSP tracks when their times differ by <=2 hours.",
        "- Draw DMSP ion drift as arrows with length proportional to speed.",
        "",
        "Coordinate handling:",
        "- GUVI and DMSP geographic positions were converted with aacgmv2 2.7.1.",
        "- SSUSI background uses the product magnetic grid/MLT, plotted in the same polar MLT geometry.",
        "",
    ]
    if not candidates.empty:
        lines.append("Top 12-18 MLT candidate windows using a 4-hour tolerance:")
        for i, row in candidates.head(8).iterrows():
            lines.append(
                f"{i+1:02d}. center={row.center_ut:.2f} UT, window={row.start_ut:.2f}-{row.end_ut:.2f} UT, "
                f"GUVI n={int(row.guvi_n)}, median O/N2={row.guvi_on2_median:.3f}, min={row.guvi_on2_min:.3f}; "
                f"DMSP westward n={int(row.dmsp_westward_n)}, p95={row.dmsp_westward_p95_kms:.2f}, "
                f"max={row.dmsp_westward_max_kms:.2f} km/s, score={row.score:.2f}"
            )
        lines.append("")

    lines.extend(
        [
            "Selected SSUSI/SuperDARN overlap:",
            f"- SSUSI file: {orbit.path.name}",
            f"- Satellite/rev: {orbit.sat} REV {orbit.rev}",
            f"- SSUSI 12-18 MLT valid UT: {orbit.ut_min:.3f}-{orbit.ut_max:.3f}",
            f"- SuperDARN quick-look: {SUPERDARN_IMAGE.name}, selected panel {superdarn_info['panel_window'][0]:.3f}-{superdarn_info['panel_window'][1]:.3f} UT",
            f"- SuperDARN track overlay window: {superdarn_info['track_window'][0]:.3f}-{superdarn_info['track_window'][1]:.3f} UT (SSUSI +/-2 h)",
            f"- SuperDARN GUVI count in 12-18 MLT overlay: {superdarn_info['guvi_counts'][0]}",
            f"- SuperDARN DMSP count in 12-18 MLT overlay: {superdarn_info['dmsp_counts'][0]}",
            "",
        ]
    )
    lines.extend(describe_mask("SuperDARN-overlaid GUVI", guvi, superdarn_info["guvi_mask"], "on2"))
    lines.extend(describe_mask("SuperDARN-overlaid DMSP", dmsp, superdarn_info["dmsp_mask"], "horizontal_ion_drift_mps"))
    lines.extend(describe_mask("SSUSI-overlaid GUVI (<=2 h from SSUSI)", guvi, ssusi_info["guvi_mask"], "on2"))
    lines.extend(describe_mask("SSUSI-overlaid DMSP", dmsp, ssusi_info["dmsp_mask"], "horizontal_ion_drift_mps"))
    lines.extend(
        [
            "",
            "Outputs:",
            f"- SuperDARN base map overlay: {superdarn_out.name}",
            f"- DMSP-SSUSI base map overlay: {ssusi_out.name}",
        ]
    )
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main() -> None:
    SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    candidates_csv = SCRIPT_DIR / "lt12_18_overlap_candidates_aacgm.csv"

    guvi = read_guvi_aacgm()
    dmsp = read_dmsp_aacgm()
    candidates = scan_overlap_windows(guvi, dmsp)
    candidates.to_csv(candidates_csv, index=False)

    orbit = select_ssusi_orbit(guvi, dmsp)
    superdarn_out, superdarn_info = plot_superdarn(guvi, dmsp, orbit)
    ssusi_out, ssusi_info = plot_ssusi(orbit, guvi, dmsp)
    summary = write_summary(candidates, orbit, superdarn_out, superdarn_info, ssusi_out, ssusi_info, guvi, dmsp)

    print(f"Candidates: {candidates_csv}")
    print(f"Selected SSUSI: {orbit.path.name} score={orbit.score:.2f}")
    print(f"SuperDARN figure: {superdarn_out}")
    print(f"SSUSI figure: {ssusi_out}")
    print(f"Summary: {summary}")


if __name__ == "__main__":
    main()

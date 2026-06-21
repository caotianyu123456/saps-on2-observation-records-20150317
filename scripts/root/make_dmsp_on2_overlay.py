import csv
import gzip
from pathlib import Path

import matplotlib.pyplot as plt
import netCDF4
import numpy as np


ROOT = Path(__file__).resolve().parent

GUVI_17 = ROOT / "timed_guvi_l3-on2_2015076_Av0100r000.nc"
GUVI_16 = ROOT / "timed_guvi_l3-on2_2015075_Av0100r000.nc"
DMSP_FILES = {
    "F17": ROOT / "dmsp_f17_ssies_20150317.EDR.gz",
    "F18": ROOT / "dmsp_f18_ssies_20150317.EDR.gz",
}


def wrap_pm180(lon):
    return ((lon + 180.0) % 360.0) - 180.0


def lon_to_lt_at_ut(lon, ut_hour=9.0):
    return (ut_hour + lon / 15.0) % 24.0


def circular_interp(values, seconds):
    radians = np.deg2rad(np.asarray(values, dtype=float))
    unwrapped = np.unwrap(radians)
    interp = np.interp(seconds, [0, 20, 40], unwrapped)
    tail = seconds > 40
    if np.any(tail):
        slope = (unwrapped[2] - unwrapped[1]) / 20.0
        interp[tail] = unwrapped[2] + (seconds[tail] - 40.0) * slope
    return np.rad2deg(interp)


def linear_interp(values, seconds):
    values = np.asarray(values, dtype=float)
    interp = np.interp(seconds, [0, 20, 40], values)
    tail = seconds > 40
    if np.any(tail):
        slope = (values[2] - values[1]) / 20.0
        interp[tail] = values[2] + (seconds[tail] - 40.0) * slope
    return interp


def parse_float_block(lines):
    vals = []
    for line in lines:
        vals.extend(float(x) for x in line.split())
    return np.asarray(vals, dtype=float)


def parse_ssies_edr(path, satellite):
    with gzip.open(path, "rt", errors="replace") as handle:
        lines = handle.readlines()

    records = []
    starts = [i - 1 for i, line in enumerate(lines) if "RECORD, EDR OF RECORD" in line]
    for pos, start in enumerate(starts):
        end = starts[pos + 1] if pos + 1 < len(starts) else len(lines)
        chunk = [line.rstrip() for line in lines[start:end]]
        if len(chunk) < 45 or "DMSP #" not in chunk[1]:
            continue

        meta = chunk[2].split()
        if len(meta) < 5:
            continue
        date = meta[3]
        hhmm = meta[4].zfill(4)
        hour = int(hhmm[:2])
        minute = int(hhmm[2:])

        eph = np.array([[float(x) for x in chunk[i].split()] for i in [4, 5, 6]])
        horiz = parse_float_block(chunk[23:33])
        seconds = np.arange(60, dtype=float)

        glat = linear_interp(eph[:, 0], seconds)
        glon = wrap_pm180(circular_interp(eph[:, 1], seconds))
        apex_lat = linear_interp(eph[:, 2], seconds)
        apex_lon = wrap_pm180(circular_interp(eph[:, 3], seconds))
        apex_mlt = (circular_interp(eph[:, 4] * 15.0, seconds) / 15.0) % 24.0
        alt_km = linear_interp(eph[:, 5], seconds)

        for sec, drift in enumerate(horiz[:60]):
            if abs(drift) > 1e30:
                continue
            ut = hour + minute / 60.0 + sec / 3600.0
            idx = int(sec)
            records.append(
                {
                    "satellite": satellite,
                    "ut": ut,
                    "glt": (ut + glon[idx] / 15.0) % 24.0,
                    "glat": glat[idx],
                    "glon": glon[idx],
                    "lt9": lon_to_lt_at_ut(glon[idx], 9.0),
                    "apex_lat": apex_lat[idx],
                    "apex_lon": apex_lon[idx],
                    "apex_mlt": apex_mlt[idx],
                    "alt_km": alt_km[idx],
                    "horizontal_ion_drift_mps": drift,
                    "time_iso": (
                        f"{date[:4]}-{date[4:6]}-{date[6:8]}"
                        f"T{hour:02d}:{minute:02d}:{sec:02d}"
                    ),
                }
            )
    return records


def write_csv(path, records):
    fields = [
        "satellite",
        "ut",
        "glt",
        "glat",
        "glon",
        "lt9",
        "apex_lat",
        "apex_lon",
        "apex_mlt",
        "alt_km",
        "horizontal_ion_drift_mps",
        "time_iso",
    ]
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def read_guvi_grid(path):
    ds = netCDF4.Dataset(path)
    lon = np.asarray(ds.variables["GRID_LONGITUDE"][:], dtype=float)
    lat = np.asarray(ds.variables["GRID_LATITUDE"][:], dtype=float)
    on2 = np.asarray(ds.variables["ON2_GRID_INTERPOLATED"][:], dtype=float)
    ds.close()

    on2 = np.ma.masked_invalid(on2)
    on2 = np.ma.masked_where(np.abs(on2) > 1e20, on2)
    return lon, lat, on2


def sort_grid_by_lt(lon, grid, ut_hour=9.0):
    lt = lon_to_lt_at_ut(lon, ut_hour)
    order = np.argsort(lt)
    return lt[order], grid[:, order]


def to_columns(records):
    cols = {}
    for key in records[0]:
        if key in {"satellite", "time_iso"}:
            cols[key] = np.array([r[key] for r in records])
        else:
            cols[key] = np.array([r[key] for r in records], dtype=float)
    return cols


def mask_window(cols, lat_range=(40, 70), lt9_range=(18, 24)):
    return (
        (cols["glat"] >= lat_range[0])
        & (cols["glat"] <= lat_range[1])
        & (cols["lt9"] >= lt9_range[0])
        & (cols["lt9"] <= lt9_range[1])
    )


def mask_mlt_dusk(cols, lat_range=(40, 70), mlt_range=(17, 24)):
    return (
        (cols["glat"] >= lat_range[0])
        & (cols["glat"] <= lat_range[1])
        & (cols["apex_mlt"] >= mlt_range[0])
        & (cols["apex_mlt"] <= mlt_range[1])
    )


def grid_drift(cols, mask, lt_bins, lat_bins, use_abs=False):
    x = cols["lt9"][mask]
    y = cols["glat"][mask]
    z = cols["horizontal_ion_drift_mps"][mask]
    if use_abs:
        z = np.abs(z)
    out = np.full((len(lat_bins) - 1, len(lt_bins) - 1), np.nan)
    counts = np.zeros_like(out, dtype=int)
    values = [[[] for _ in range(len(lt_bins) - 1)] for _ in range(len(lat_bins) - 1)]
    xi = np.digitize(x, lt_bins) - 1
    yi = np.digitize(y, lat_bins) - 1
    for i, j, val in zip(yi, xi, z):
        if 0 <= i < out.shape[0] and 0 <= j < out.shape[1]:
            values[i][j].append(val)
            counts[i, j] += 1
    for i in range(out.shape[0]):
        for j in range(out.shape[1]):
            if values[i][j]:
                out[i, j] = np.nanmedian(values[i][j])
    return np.ma.masked_invalid(out), counts


def add_boxes(ax):
    for x0, x1, y0, y1, color, ls, label in [
        (18, 24, 40, 70, "#ff7f0e", "--", "9 UT 18-24 LT sector"),
        (19, 23, 40, 70, "#d62728", "-", "core SAPS analysis sector"),
    ]:
        ax.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], color=color, lw=2.0, ls=ls, label=label)


def summarize(label, records):
    cols = to_columns(records)
    geo = mask_window(cols)
    mlt = mask_mlt_dusk(cols)
    print(f"{label}: samples={len(records)}")
    for name, mask in [("geo 40-70N, LT9 18-24", geo), ("geo 40-70N, apex MLT 17-24", mlt)]:
        n = int(mask.sum())
        print(f"  {name}: n={n}")
        if n:
            drift = cols["horizontal_ion_drift_mps"][mask]
            print(
                "    UT={:.2f}-{:.2f}, GLT={:.2f}-{:.2f}, lon={:.1f}-{:.1f}, "
                "lat={:.1f}-{:.1f}, drift median={:.0f}, min={:.0f}, max={:.0f}".format(
                    cols["ut"][mask].min(),
                    cols["ut"][mask].max(),
                    cols["glt"][mask].min(),
                    cols["glt"][mask].max(),
                    cols["glon"][mask].min(),
                    cols["glon"][mask].max(),
                    cols["glat"][mask].min(),
                    cols["glat"][mask].max(),
                    np.nanmedian(drift),
                    np.nanmin(drift),
                    np.nanmax(drift),
                )
            )
    return cols


def main():
    all_records = []
    for sat, path in DMSP_FILES.items():
        records = parse_ssies_edr(path, sat)
        write_csv(ROOT / f"dmsp_{sat.lower()}_ssies_20150317_parsed.csv", records)
        summarize(sat, records)
        all_records.extend(records)

    cols = to_columns(all_records)
    lon, lat, on2_17 = read_guvi_grid(GUVI_17)
    _, _, on2_16 = read_guvi_grid(GUVI_16)
    delta = on2_17 - on2_16
    lt, delta_lt = sort_grid_by_lt(lon, delta)

    fig, ax = plt.subplots(figsize=(13.5, 6.0), dpi=180)
    mesh = ax.pcolormesh(lt, lat, delta_lt, shading="auto", cmap="RdBu_r", vmin=-0.8, vmax=0.8)
    cbar = fig.colorbar(mesh, ax=ax, pad=0.01)
    cbar.set_label("GUVI O/N2 anomaly (17 Mar - 16 Mar)")
    add_boxes(ax)

    plot_mask = (
        (cols["glat"] >= 35)
        & (cols["glat"] <= 75)
        & (cols["lt9"] >= 0)
        & (cols["lt9"] <= 24)
        & (np.abs(cols["horizontal_ion_drift_mps"]) <= 5000)
    )
    sc = ax.scatter(
        cols["lt9"][plot_mask],
        cols["glat"][plot_mask],
        c=cols["horizontal_ion_drift_mps"][plot_mask],
        s=12,
        cmap="PiYG_r",
        vmin=-3000,
        vmax=3000,
        edgecolors="k",
        linewidths=0.15,
        alpha=0.88,
        label="DMSP SSIES horizontal ion drift",
    )
    cbar2 = fig.colorbar(sc, ax=ax, pad=0.055)
    cbar2.set_label("Horizontal ion drift (m/s)")

    ax.set_xlim(0, 24)
    ax.set_ylim(0, 80)
    ax.set_xticks(np.arange(0, 25, 3))
    ax.set_xlabel("Geographic longitude converted to LT at 9 UT (hours)")
    ax.set_ylabel("Geographic latitude (deg)")
    ax.set_title("DMSP SSIES ion drift over observed GUVI O/N2 depletion sector, 17 March 2015")
    ax.grid(alpha=0.22)
    ax.legend(loc="lower left", framealpha=0.9)
    ax.text(
        0.01,
        0.98,
        "Background: TIMED/GUVI gridded O/N2 anomaly. Symbols: DMSP F17/F18 SSIES drift by geographic position.\n"
        "Note: satellite samples are observed at their own UT/MLT; x-axis maps longitude to the same 9 UT LT frame as the SAPS sector box.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        bbox=dict(fc="white", ec="0.45", alpha=0.82, boxstyle="round,pad=0.35"),
    )
    fig.tight_layout()
    fig.savefig(ROOT / "guvi_on2_dmsp_drift_overlay_lt9.png")
    plt.close(fig)

    lat_bins = np.arange(40, 70.1, 2.0)
    lt_bins = np.arange(18, 24.01, 0.5)
    geo_mask = mask_window(cols, (40, 70), (18, 24))
    drift_grid, counts = grid_drift(cols, geo_mask, lt_bins, lat_bins)

    fig, ax = plt.subplots(figsize=(10.5, 5.3), dpi=180)
    focused = (lt >= 17) & (lt <= 24)
    bg = ax.pcolormesh(lt[focused], lat, delta_lt[:, focused], shading="auto", cmap="RdBu_r", vmin=-0.8, vmax=0.8)
    cbar = fig.colorbar(bg, ax=ax, pad=0.01)
    cbar.set_label("GUVI O/N2 anomaly")
    add_boxes(ax)
    if drift_grid.count() > 0:
        xs = 0.5 * (lt_bins[:-1] + lt_bins[1:])
        ys = 0.5 * (lat_bins[:-1] + lat_bins[1:])
        xx, yy = np.meshgrid(xs, ys)
        sc = ax.scatter(
            xx[~drift_grid.mask],
            yy[~drift_grid.mask],
            c=drift_grid.compressed(),
            marker="s",
            s=95,
            cmap="PiYG_r",
            vmin=-3000,
            vmax=3000,
            edgecolors="k",
            linewidths=0.25,
        )
        cbar2 = fig.colorbar(sc, ax=ax, pad=0.055)
        cbar2.set_label("Binned DMSP drift (m/s)")
    else:
        ax.text(
            20.9,
            55,
            "No F17/F18 SSIES samples\ninside this geographic box",
            ha="center",
            va="center",
            fontsize=12,
            bbox=dict(fc="white", ec="0.45", alpha=0.9, boxstyle="round,pad=0.35"),
        )
    ax.set_xlim(17, 24)
    ax.set_ylim(35, 75)
    ax.set_xlabel("Geographic longitude converted to LT at 9 UT (hours)")
    ax.set_ylabel("Geographic latitude (deg)")
    ax.set_title("Direct DMSP coverage inside the 9 UT SAPS-related geographic sector")
    ax.grid(alpha=0.22)
    fig.tight_layout()
    fig.savefig(ROOT / "guvi_on2_dmsp_drift_overlay_lt9_corebox.png")
    plt.close(fig)

    speed_grid, speed_counts = grid_drift(cols, geo_mask, lt_bins, lat_bins, use_abs=True)
    fig, ax = plt.subplots(figsize=(10.5, 5.3), dpi=180)
    bg = ax.pcolormesh(lt[focused], lat, delta_lt[:, focused], shading="auto", cmap="RdBu_r", vmin=-0.8, vmax=0.8)
    cbar = fig.colorbar(bg, ax=ax, pad=0.01)
    cbar.set_label("GUVI O/N2 anomaly")
    add_boxes(ax)
    if speed_grid.count() > 0:
        xs = 0.5 * (lt_bins[:-1] + lt_bins[1:])
        ys = 0.5 * (lat_bins[:-1] + lat_bins[1:])
        xx, yy = np.meshgrid(xs, ys)
        sc = ax.scatter(
            xx[~speed_grid.mask],
            yy[~speed_grid.mask],
            c=speed_grid.compressed(),
            marker="s",
            s=105,
            cmap="magma_r",
            vmin=0,
            vmax=3000,
            edgecolors="k",
            linewidths=0.25,
        )
        cbar2 = fig.colorbar(sc, ax=ax, pad=0.055)
        cbar2.set_label("Binned |DMSP horizontal drift| (m/s)")
    ax.set_xlim(17, 24)
    ax.set_ylim(35, 75)
    ax.set_xlabel("Geographic longitude converted to LT at 9 UT (hours)")
    ax.set_ylabel("Geographic latitude (deg)")
    ax.set_title("Observed O/N2 depletion with gridded DMSP ion-drift speed")
    ax.text(
        0.02,
        0.98,
        "DMSP F17/F18 SSIES, 17 Mar 2015, binned by geographic position.\n"
        "Speed is |horizontal ion drift|; samples are not simultaneous 9 UT overpasses.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        bbox=dict(fc="white", ec="0.45", alpha=0.86, boxstyle="round,pad=0.35"),
    )
    ax.grid(alpha=0.22)
    fig.tight_layout()
    fig.savefig(ROOT / "guvi_on2_dmsp_speed_overlay_lt9_corebox.png")
    plt.close(fig)

    mlt_mask = mask_mlt_dusk(cols, (40, 70), (17, 24))
    fig, ax = plt.subplots(figsize=(11.0, 5.4), dpi=180)
    bg = ax.pcolormesh(lt, lat, delta_lt, shading="auto", cmap="RdBu_r", vmin=-0.8, vmax=0.8)
    cbar = fig.colorbar(bg, ax=ax, pad=0.01)
    cbar.set_label("GUVI O/N2 anomaly")
    add_boxes(ax)
    sc = ax.scatter(
        cols["lt9"][mlt_mask],
        cols["glat"][mlt_mask],
        c=cols["horizontal_ion_drift_mps"][mlt_mask],
        s=17,
        cmap="PiYG_r",
        vmin=-3000,
        vmax=3000,
        edgecolors="k",
        linewidths=0.15,
        alpha=0.9,
    )
    cbar2 = fig.colorbar(sc, ax=ax, pad=0.055)
    cbar2.set_label("Horizontal ion drift (m/s)")
    ax.set_xlim(0, 24)
    ax.set_ylim(35, 75)
    ax.set_xticks(np.arange(0, 25, 3))
    ax.set_xlabel("Geographic longitude converted to LT at 9 UT (hours)")
    ax.set_ylabel("Geographic latitude (deg)")
    ax.set_title("DMSP dusk-sector SAPS observations in magnetic MLT, plotted by geographic position")
    ax.text(
        0.01,
        0.98,
        "Filtered points: geographic 40-70N and Apex MLT 17-24.\n"
        "This follows the SAPS definition used in the JGR comparison, but it is not identical to the 9 UT geographic LT box.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        bbox=dict(fc="white", ec="0.45", alpha=0.85, boxstyle="round,pad=0.35"),
    )
    ax.grid(alpha=0.22)
    fig.tight_layout()
    fig.savefig(ROOT / "guvi_on2_dmsp_drift_overlay_magnetic_dusk.png")
    plt.close(fig)


if __name__ == "__main__":
    main()

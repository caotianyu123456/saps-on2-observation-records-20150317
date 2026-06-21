import datetime as dt
import os
import sys
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
import pandas as pd
from PIL import Image

from make_guvi_dmsp_mlt_candidate import GUVI_FILES, read_dmsp
from make_guvi_dmsp_westward_saps_window import read_guvi_raw_cd


ROOT = Path(__file__).resolve().parent
LOCAL_DEPS = ROOT / ".codex_deps"
LOCAL_HOME = ROOT / ".codex_home"
OMNI_CACHE = ROOT / "omni_hro_1min_20150316_20150318.csv"

SUPERDARN_URL = (
    "https://sdc-serv.usask.ca/convection_plots/2015/03/"
    "convection_maps_s_20150317_223800.png"
)
SUPERDARN_IMAGE = ROOT / "convection_maps_s_20150317_223800.png"
SUPERDARN_PANELS = [
    {"center": (392.0, 397.0), "radius": 277.0, "window": (22 + 30 / 60, 22 + 32 / 60)},
    {"center": (1208.0, 397.0), "radius": 277.0, "window": (22 + 32 / 60, 22 + 34 / 60)},
    {"center": (392.0, 1165.0), "radius": 277.0, "window": (22 + 34 / 60, 22 + 36 / 60)},
    {"center": (1208.0, 1165.0), "radius": 277.0, "window": (22 + 36 / 60, 22 + 38 / 60)},
    {"center": (800.0, 1934.0), "radius": 277.0, "window": (22 + 38 / 60, 22 + 40 / 60)},
]


def prepare_local_runtime():
    LOCAL_HOME.mkdir(exist_ok=True)
    (LOCAL_HOME / "Geospacelab" / "Data").mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HOME", str(LOCAL_HOME))
    os.environ.setdefault("USERPROFILE", str(LOCAL_HOME))
    if LOCAL_DEPS.exists():
        sys.path.insert(0, str(LOCAL_DEPS))


def fetch_omni_if_needed():
    if OMNI_CACHE.exists():
        return clean_omni(pd.read_csv(OMNI_CACHE, parse_dates=["Epoch"]))

    prepare_local_runtime()
    from cdasws import CdasWs

    variables = ["BZ_GSM", "BY_GSM", "flow_speed", "Pressure", "E", "AE_INDEX", "SYM_H"]
    status, data = CdasWs().get_data(
        "OMNI_HRO_1MIN",
        variables,
        "2015-03-16T00:00:00Z",
        "2015-03-18T23:59:00Z",
    )
    if status.get("http", {}).get("status_code") != 200:
        raise RuntimeError(f"CDAWeb request failed: {status}")
    frame = pd.DataFrame({"Epoch": pd.to_datetime(data["Epoch"])})
    for var in variables:
        values = np.asarray(data[var], dtype=float)
        values[np.abs(values) > 1e20] = np.nan
        frame[var] = values

    frame = clean_omni(frame)
    frame.to_csv(OMNI_CACHE, index=False)
    return frame


def clean_omni(frame):
    frame = frame.copy()
    # Conservative fill-value cleanup for OMNI HRO variables.
    frame.loc[frame["flow_speed"] > 5000, "flow_speed"] = np.nan
    frame.loc[frame["Pressure"] >= 80, "Pressure"] = np.nan
    frame.loc[np.abs(frame["E"]) > 500, "E"] = np.nan
    frame.loc[np.abs(frame["AE_INDEX"]) > 20000, "AE_INDEX"] = np.nan
    frame.loc[np.abs(frame["SYM_H"]) > 20000, "SYM_H"] = np.nan
    frame.loc[np.abs(frame["BZ_GSM"]) > 500, "BZ_GSM"] = np.nan
    frame.loc[np.abs(frame["BY_GSM"]) > 500, "BY_GSM"] = np.nan
    return frame


def plot_event_context(omni):
    out = ROOT / "geospacelab_style_20150317_event_context.png"
    t0 = pd.Timestamp("2015-03-16 00:00")
    t1 = pd.Timestamp("2015-03-18 23:59")
    overlay_start = pd.Timestamp("2015-03-17 22:30")
    overlay_end = pd.Timestamp("2015-03-17 22:40")

    fig, axes = plt.subplots(4, 1, figsize=(10.8, 8.2), dpi=220, sharex=True)
    fig.subplots_adjust(left=0.085, right=0.90, top=0.91, bottom=0.10, hspace=0.16)

    ax = axes[0]
    ax.plot(omni["Epoch"], omni["BZ_GSM"], color="#2455a4", lw=0.9, label="Bz GSM")
    ax.plot(omni["Epoch"], omni["BY_GSM"], color="#9b2f2f", lw=0.75, alpha=0.88, label="By GSM")
    ax.axhline(0, color="0.25", lw=0.6)
    ax.set_ylabel("IMF (nT)")
    ax.legend(loc="upper right", ncol=2, fontsize=8, frameon=True)

    ax = axes[1]
    ax.plot(omni["Epoch"], omni["flow_speed"], color="#376b39", lw=0.9, label="Vsw")
    ax.set_ylabel("Vsw (km/s)")
    ax2 = ax.twinx()
    ax2.plot(omni["Epoch"], omni["Pressure"], color="#ba6b18", lw=0.75, alpha=0.82, label="Pdyn")
    ax2.set_ylabel("Pdyn (nPa)")
    ax.legend(loc="upper left", fontsize=8, frameon=True)
    ax2.legend(loc="upper right", fontsize=8, frameon=True)

    ax = axes[2]
    ax.plot(omni["Epoch"], omni["E"], color="#5d3a9b", lw=0.9)
    ax.axhline(0, color="0.25", lw=0.6)
    ax.set_ylabel("Ey (mV/m)")

    ax = axes[3]
    ax.plot(omni["Epoch"], omni["SYM_H"], color="#262626", lw=0.9, label="SYM-H")
    ax.set_ylabel("SYM-H (nT)")
    ax2 = ax.twinx()
    ax2.plot(omni["Epoch"], omni["AE_INDEX"], color="#d54c2b", lw=0.60, alpha=0.74, label="AE")
    ax2.set_ylabel("AE (nT)")
    ax.legend(loc="lower left", fontsize=8, frameon=True)
    ax2.legend(loc="upper right", fontsize=8, frameon=True)

    for ax in axes:
        ax.axvspan(overlay_start, overlay_end, color="#f2c84b", alpha=0.36, lw=0)
        ax.grid(alpha=0.24, lw=0.55)
        ax.set_xlim(t0, t1)
    axes[-1].xaxis.set_major_locator(mdates.HourLocator(interval=6))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%m-%d\n%H UT"))
    axes[-1].set_xlabel("Universal Time")
    fig.suptitle("17 Mar 2015 Storm Context from CDAWeb OMNI HRO 1-min", fontsize=13)
    fig.text(
        0.086,
        0.935,
        "Yellow shading: SuperDARN/GUVI overlay interval, 2015-03-17 22:30-22:40 UT",
        fontsize=8.4,
        color="0.28",
    )
    fig.savefig(out)
    plt.close(fig)
    return out


def mlat_mlt_to_pixels(mlat, mlt, center, radius):
    abs_mlat = np.abs(np.asarray(mlat, dtype=float))
    mlt = np.asarray(mlt, dtype=float)
    rho = (90.0 - abs_mlat) / 40.0 * radius
    theta = 2.0 * np.pi * (mlt - 6.0) / 24.0
    return center[0] + rho * np.cos(theta), center[1] - rho * np.sin(theta)


def split_large_jumps(x, y, max_jump=70.0):
    groups = []
    if len(x) == 0:
        return groups
    start = 0
    for i in range(1, len(x)):
        if np.hypot(x[i] - x[i - 1], y[i] - y[i - 1]) > max_jump:
            groups.append((x[start:i], y[start:i]))
            start = i
    groups.append((x[start:], y[start:]))
    return groups


def plot_superdarn_guvi_dmsp_overlay():
    if not SUPERDARN_IMAGE.exists():
        raise FileNotFoundError(
            f"Missing {SUPERDARN_IMAGE.name}; download it from {SUPERDARN_URL}"
        )

    guvi = read_guvi_raw_cd(GUVI_FILES["17 Mar"])
    dmsp = read_dmsp()
    image = np.asarray(Image.open(SUPERDARN_IMAGE).convert("RGB"))
    height, width = image.shape[:2]

    fig, ax = plt.subplots(figsize=(width / 190, height / 190), dpi=190)
    ax.imshow(image, extent=(0, width, height, 0))
    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)
    ax.axis("off")

    guvi_mask_all = np.zeros_like(guvi["ut"], dtype=bool)
    dmsp_mask_all = np.zeros_like(dmsp["ut"], dtype=bool)
    guvi_scatter = None
    dmsp_scatter = None
    guvi_counts = []
    dmsp_counts = []

    for panel in SUPERDARN_PANELS:
        start, end = panel["window"]
        guvi_mask = (
            (guvi["ut"] >= start)
            & (guvi["ut"] < end)
            & (guvi["mlat"] <= -45.0)
            & (guvi["mlat"] >= -80.0)
        )
        guvi_mask_all |= guvi_mask
        guvi_counts.append(int(guvi_mask.sum()))
        if np.any(guvi_mask):
            idx = np.where(guvi_mask)[0]
            idx = idx[np.argsort(guvi["ut"][idx])]
            x, y = mlat_mlt_to_pixels(guvi["mlat"][idx], guvi["mlt"][idx], panel["center"], panel["radius"])
            for xs, ys in split_large_jumps(x, y):
                if len(xs) >= 2:
                    ax.plot(
                        xs,
                        ys,
                        color="white",
                        lw=3.8,
                        alpha=0.95,
                        solid_capstyle="round",
                        zorder=20,
                        path_effects=[pe.Stroke(linewidth=6.1, foreground="black", alpha=0.55), pe.Normal()],
                    )
            guvi_scatter = ax.scatter(
                x,
                y,
                c=guvi["on2"][idx],
                cmap="viridis",
                vmin=0,
                vmax=1.1,
                s=26,
                edgecolor="black",
                linewidth=0.45,
                zorder=22,
            )

        dmsp_mask = (
            (dmsp["ut"] >= start)
            & (dmsp["ut"] < end)
            & (dmsp["cd_mlat"] <= -45.0)
            & (dmsp["cd_mlat"] >= -80.0)
        )
        dmsp_mask_all |= dmsp_mask
        dmsp_counts.append(int(dmsp_mask.sum()))
        if np.any(dmsp_mask):
            idx = np.where(dmsp_mask)[0]
            idx = idx[np.argsort(dmsp["ut"][idx])]
            if len(idx) > 120:
                idx = idx[np.linspace(0, len(idx) - 1, 120, dtype=int)]
            x, y = mlat_mlt_to_pixels(dmsp["cd_mlat"][idx], dmsp["cd_mlt"][idx], panel["center"], panel["radius"])
            dmsp_scatter = ax.scatter(
                x,
                y,
                c=dmsp["horizontal_ion_drift_mps"][idx] / 1000.0,
                cmap="coolwarm",
                vmin=-2.0,
                vmax=2.0,
                marker="^",
                s=14,
                edgecolor="0.15",
                linewidth=0.25,
                alpha=0.88,
                zorder=23,
            )

    ax.text(
        80,
        2286,
        "TIMED/GUVI O/N2 track and DMSP SSIES drift, time-matched to each 2-min SuperDARN panel",
        fontsize=10.8,
        color="black",
        bbox=dict(facecolor="white", edgecolor="0.45", alpha=0.88, boxstyle="round,pad=0.28"),
        zorder=40,
    )
    ax.text(
        80,
        2330,
        "Base: SuperDARN Canada southern convection quick-look, 2015-03-17 22:30-22:40 UT. "
        "Coordinates use centered-dipole MLT/MLAT for screening.",
        fontsize=7.8,
        color="0.16",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.82, boxstyle="round,pad=0.24"),
        zorder=40,
    )

    if guvi_scatter is not None:
        cax = fig.add_axes([0.66, 0.033, 0.16, 0.010])
        cb = fig.colorbar(guvi_scatter, cax=cax, orientation="horizontal")
        cb.set_label("GUVI O/N2", fontsize=7.8)
        cb.ax.tick_params(labelsize=7)
    if dmsp_scatter is not None:
        cax = fig.add_axes([0.66, 0.073, 0.16, 0.010])
        cb = fig.colorbar(dmsp_scatter, cax=cax, orientation="horizontal")
        cb.set_label("DMSP horizontal drift (km/s, + westward)", fontsize=7.8)
        cb.ax.tick_params(labelsize=7)

    out = ROOT / "geospacelab_style_superdarn_guvi_dmsp_20150317_south.png"
    fig.savefig(out, dpi=190)
    plt.close(fig)

    return out, {
        "guvi": guvi,
        "dmsp": dmsp,
        "guvi_mask": guvi_mask_all,
        "dmsp_mask": dmsp_mask_all,
        "guvi_counts": guvi_counts,
        "dmsp_counts": dmsp_counts,
    }


def summarize_outputs(omni, context_path, overlay_path, overlay_info):
    guvi = overlay_info["guvi"]
    dmsp = overlay_info["dmsp"]
    gm = overlay_info["guvi_mask"]
    dm = overlay_info["dmsp_mask"]
    storm_day = (omni["Epoch"] >= "2015-03-17") & (omni["Epoch"] < "2015-03-18")
    sym_min_idx = omni.loc[storm_day, "SYM_H"].idxmin()
    bz_min_idx = omni.loc[storm_day, "BZ_GSM"].idxmin()
    ae_max_idx = omni.loc[storm_day, "AE_INDEX"].idxmax()

    lines = [
        "GeospaceLAB-style 17 Mar 2015 observation figure set",
        "",
        f"Installed/used local helper packages from: {LOCAL_DEPS}",
        "Note: aacgmv2 could not be installed on this Windows Python because Microsoft C++ Build Tools are absent; centered-dipole MLT/MLAT is used for screening overlays.",
        "",
        "Outputs:",
        f"- Event context: {context_path.name}",
        f"- SuperDARN/GUVI/DMSP overlay: {overlay_path.name}",
        "",
        "OMNI HRO 1-min storm-day highlights:",
        f"- Minimum SYM-H: {omni.loc[sym_min_idx, 'SYM_H']:.0f} nT at {omni.loc[sym_min_idx, 'Epoch']} UT",
        f"- Minimum Bz GSM: {omni.loc[bz_min_idx, 'BZ_GSM']:.1f} nT at {omni.loc[bz_min_idx, 'Epoch']} UT",
        f"- Maximum AE: {omni.loc[ae_max_idx, 'AE_INDEX']:.0f} nT at {omni.loc[ae_max_idx, 'Epoch']} UT",
        "",
        "SuperDARN/GUVI/DMSP overlay interval:",
        "- Base SuperDARN quick-look URL: " + SUPERDARN_URL,
        "- Interval: 2015-03-17 22:30-22:40 UT, southern hemisphere, five 2-min panels.",
        f"- GUVI points per panel: {overlay_info['guvi_counts']}",
        f"- DMSP points per panel after polar-map filtering: {overlay_info['dmsp_counts']}",
    ]
    if np.any(gm):
        lines.append(
            f"- GUVI overlaid: n={int(gm.sum())}, UT={np.nanmin(guvi['ut'][gm]):.3f}-{np.nanmax(guvi['ut'][gm]):.3f}, "
            f"CD-MLAT={np.nanmin(guvi['mlat'][gm]):.1f}..{np.nanmax(guvi['mlat'][gm]):.1f}, "
            f"CD-MLT={np.nanmin(guvi['mlt'][gm]):.1f}..{np.nanmax(guvi['mlt'][gm]):.1f}, "
            f"O/N2 median={np.nanmedian(guvi['on2'][gm]):.3f}, min={np.nanmin(guvi['on2'][gm]):.3f}."
        )
    if np.any(dm):
        drift = dmsp["horizontal_ion_drift_mps"][dm] / 1000.0
        lines.append(
            f"- DMSP overlaid: n={int(dm.sum())}, drift median={np.nanmedian(drift):.2f} km/s, "
            f"p95={np.nanpercentile(drift, 95):.2f} km/s, max={np.nanmax(drift):.2f} km/s; positive is treated as westward."
        )
    lines.extend(
        [
            "",
            "Interpretive note:",
            "The 22:30-22:40 UT southern SuperDARN quick-look shows a coherent dusk-side/subauroral convection channel while GUVI samples a depleted O/N2 track across CD-MLAT about -70 to -62 and CD-MLT about 13-17.",
            "Use this as a screening/publication-planning figure; for final publication, rerun the coordinate conversion with AACGM/Apex after installing the required compiled dependency.",
        ]
    )
    summary = ROOT / "geospacelab_style_20150317_observations_summary.txt"
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def main():
    prepare_local_runtime()
    try:
        import geospacelab  # noqa: F401
    except Exception as exc:
        print(f"GeospaceLAB import warning: {exc}")

    omni = fetch_omni_if_needed()
    context_path = plot_event_context(omni)
    overlay_path, overlay_info = plot_superdarn_guvi_dmsp_overlay()
    summary = summarize_outputs(omni, context_path, overlay_path, overlay_info)
    print(context_path)
    print(overlay_path)
    print(summary)


if __name__ == "__main__":
    main()

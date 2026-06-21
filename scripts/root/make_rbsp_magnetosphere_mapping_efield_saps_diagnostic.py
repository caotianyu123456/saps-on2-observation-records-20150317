from pathlib import Path
import csv

import cdflib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Patch


ROOT = Path(__file__).resolve().parent
RE_KM = 6371.2
SUBAURORAL_ABS_MLAT = (48.0, 70.0)
SAPS_MLT = (15.0, 24.0)
EFIELD_SCREENING_MVM = 5.0
EFIELD_STRONG_MVM = 10.0

RBSP_FILES = {
    "A": {
        "efw": ROOT
        / "rbsp_data/rbspa/l2/efw/e-spinfit-mgse/2015/rbspa_efw-l2_e-spinfit-mgse_20150317_v04.cdf",
        "mage": ROOT
        / "rbsp_data/rbspa/ephemeris/ect-mag-ephem/cdf/def-1min-op77q/2015/rbsp-a_mag-ephem_def-1min-op77q_20150317_v01.cdf",
    },
    "B": {
        "efw": ROOT
        / "rbsp_data/rbspb/l2/efw/e-spinfit-mgse/2015/rbspb_efw-l2_e-spinfit-mgse_20150317_v04.cdf",
        "mage": ROOT
        / "rbsp_data/rbspb/ephemeris/ect-mag-ephem/cdf/def-1min-op77q/2015/rbsp-b_mag-ephem_def-1min-op77q_20150317_v01.cdf",
    },
}


def cdf_time_to_unix_seconds(values):
    dt64 = cdflib.cdfepoch.to_datetime(values)
    return np.asarray(dt64).astype("datetime64[ns]").astype("int64") / 1e9


def unix_to_ut_hour(values):
    return ((np.asarray(values, dtype=float) - 1426550400.0) / 3600.0) % 24.0


def clean_array(values, max_abs=1e20):
    arr = np.asarray(values, dtype=float)
    arr[np.abs(arr) > max_abs] = np.nan
    return arr


def read_rbsp_probe(probe):
    paths = RBSP_FILES[probe]
    efw = cdflib.CDF(str(paths["efw"]))
    mage = cdflib.CDF(str(paths["mage"]))

    e_time = cdf_time_to_unix_seconds(efw.varget("epoch"))
    efield = clean_array(efw.varget("efield_spinfit_mgse"))
    finite_components = np.isfinite(efield)
    e_mag = np.sqrt(np.nansum(np.where(finite_components, efield, 0.0) ** 2, axis=1))
    e_mag[finite_components.sum(axis=1) == 0] = np.nan
    good = np.isfinite(e_time) & np.isfinite(e_mag) & (e_mag < 100.0)
    order = np.argsort(e_time[good])
    e_time_good = e_time[good][order]
    e_mag_good = e_mag[good][order]

    m_time = cdf_time_to_unix_seconds(mage.varget("Epoch"))
    e_on_mage = np.interp(m_time, e_time_good, e_mag_good, left=np.nan, right=np.nan)

    rgsm = clean_array(mage.varget("Rgsm"), max_abs=1e29)
    pfn_geod = clean_array(mage.varget("Pfn_geod_LatLon"), max_abs=1e29)
    pfs_geod = clean_array(mage.varget("Pfs_geod_LatLon"), max_abs=1e29)
    data = {
        "probe": probe,
        "time": m_time,
        "ut": unix_to_ut_hour(m_time),
        "e_mag": e_on_mage,
        "rgsm": rgsm,
        "pfn_mlat": clean_array(mage.varget("Pfn_CD_MLAT"), max_abs=1e29),
        "pfn_mlt": clean_array(mage.varget("Pfn_CD_MLT"), max_abs=1e29) % 24.0,
        "pfs_mlat": clean_array(mage.varget("Pfs_CD_MLAT"), max_abs=1e29),
        "pfs_mlt": clean_array(mage.varget("Pfs_CD_MLT"), max_abs=1e29) % 24.0,
        "pfn_glat": pfn_geod[:, 0],
        "pfn_glon": pfn_geod[:, 1],
        "pfs_glat": pfs_geod[:, 0],
        "pfs_glon": pfs_geod[:, 1],
    }
    data["sub_n"] = in_subauroral(data["pfn_mlat"], "N")
    data["sub_s"] = in_subauroral(data["pfs_mlat"], "S")
    data["saps_n"] = data["sub_n"] & in_mlt_sector(data["pfn_mlt"], SAPS_MLT)
    data["saps_s"] = data["sub_s"] & in_mlt_sector(data["pfs_mlt"], SAPS_MLT)
    data["sub_any"] = data["sub_n"] | data["sub_s"]
    data["saps_any"] = data["saps_n"] | data["saps_s"]
    data["candidate"] = data["saps_any"] & (data["e_mag"] >= EFIELD_SCREENING_MVM)
    return data


def in_subauroral(mlat, hemi):
    lower, upper = SUBAURORAL_ABS_MLAT
    mlat = np.asarray(mlat, dtype=float)
    if hemi == "N":
        return (mlat >= lower) & (mlat <= upper)
    return (mlat <= -lower) & (mlat >= -upper)


def in_mlt_sector(mlt, bounds):
    start, end = bounds
    mlt = np.asarray(mlt, dtype=float) % 24.0
    if start <= end:
        return (mlt >= start) & (mlt <= end)
    return (mlt >= start) | (mlt <= end)


def split_mlt_track(mlt, mlat, max_jump=6.0):
    mlt = np.asarray(mlt, dtype=float)
    mlat = np.asarray(mlat, dtype=float)
    valid = np.isfinite(mlt) & np.isfinite(mlat)
    mlt = mlt[valid]
    mlat = mlat[valid]
    if len(mlt) == 0:
        return []
    groups = []
    start = 0
    for i in range(1, len(mlt)):
        if abs(mlt[i] - mlt[i - 1]) > max_jump:
            groups.append((mlt[start:i], mlat[start:i]))
            start = i
    groups.append((mlt[start:], mlat[start:]))
    return groups


def contiguous_intervals(mask, ut, max_gap_minutes=2.5):
    mask = np.asarray(mask, dtype=bool)
    ut = np.asarray(ut, dtype=float)
    idx = np.where(mask & np.isfinite(ut))[0]
    if len(idx) == 0:
        return []
    gap_hours = max_gap_minutes / 60.0
    intervals = []
    start = idx[0]
    prev = idx[0]
    for current in idx[1:]:
        if (ut[current] - ut[prev]) > gap_hours:
            intervals.append((start, prev))
            start = current
        prev = current
    intervals.append((start, prev))
    return intervals


def interval_summary(data, mask):
    rows = []
    for start, end in contiguous_intervals(mask, data["ut"]):
        sl = slice(start, end + 1)
        e = data["e_mag"][sl]
        e = e[np.isfinite(e)]
        if len(e) == 0:
            continue
        rows.append(
            {
                "start": float(data["ut"][start]),
                "end": float(data["ut"][end]),
                "n": int(len(e)),
                "median": float(np.nanmedian(e)),
                "max": float(np.nanmax(e)),
                "p95": float(np.nanpercentile(e, 95)),
            }
        )
    return rows


def add_orbit_panel(ax, probes, norm, cmap):
    for data, marker, label in [(probes["A"], "o", "RBSP-A"), (probes["B"], "s", "RBSP-B")]:
        rgsm = data["rgsm"]
        valid = np.isfinite(rgsm[:, 0]) & np.isfinite(rgsm[:, 1]) & np.isfinite(data["e_mag"])
        ax.plot(rgsm[valid, 0], rgsm[valid, 1], color="0.35", lw=0.55, alpha=0.42, zorder=1)
        ax.scatter(
            rgsm[valid, 0],
            rgsm[valid, 1],
            c=data["e_mag"][valid],
            cmap=cmap,
            norm=norm,
            s=13 if marker == "o" else 15,
            marker=marker,
            linewidths=0,
            alpha=0.90,
            zorder=2,
            label=label,
        )
        hi = valid & data["candidate"]
        if np.any(hi):
            ax.scatter(
                rgsm[hi, 0],
                rgsm[hi, 1],
                facecolors="none",
                edgecolors="black",
                s=38 if marker == "o" else 42,
                marker=marker,
                linewidths=0.70,
                zorder=4,
            )
    ax.add_patch(Circle((0, 0), 1.0, fc="#d9d9d9", ec="black", lw=0.7, zorder=5))
    ax.axhline(0, color="0.55", lw=0.45)
    ax.axvline(0, color="0.55", lw=0.45)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("GSM X (Re)")
    ax.set_ylabel("GSM Y (Re)")
    ax.set_title("A. Magnetospheric RBSP orbit, colored by measured |E|", loc="left", fontsize=10.2)
    ax.grid(alpha=0.22)
    ax.legend(loc="upper right", fontsize=8.0, frameon=True)


def add_footpoint_panel(ax, probes, hemi, norm, cmap):
    if hemi == "N":
        lat_key = "pfn_mlat"
        mlt_key = "pfn_mlt"
        sub_range = SUBAURORAL_ABS_MLAT
        ylim = (40, 82)
        band_color = "#f2b84b"
        title = "B. Northern mapped footpoints"
    else:
        lat_key = "pfs_mlat"
        mlt_key = "pfs_mlt"
        sub_range = (-SUBAURORAL_ABS_MLAT[1], -SUBAURORAL_ABS_MLAT[0])
        ylim = (-82, -40)
        band_color = "#41b6c4"
        title = "C. Southern mapped footpoints"

    ax.axhspan(sub_range[0], sub_range[1], color=band_color, alpha=0.18, zorder=0)
    ax.axvspan(SAPS_MLT[0], SAPS_MLT[1], color="0.55", alpha=0.08, zorder=0)
    ax.text(SAPS_MLT[0] + 0.15, ylim[1] - 3.0 if hemi == "N" else ylim[0] + 3.0, "15-24 MLT", fontsize=7.4, color="0.25")

    for data, marker, line_color in [(probes["A"], "o", "#7a1688"), (probes["B"], "s", "#225ea8")]:
        valid = np.isfinite(data[mlt_key]) & np.isfinite(data[lat_key]) & np.isfinite(data["e_mag"])
        order = np.argsort(data["ut"][valid])
        x = data[mlt_key][valid][order]
        y = data[lat_key][valid][order]
        e = data["e_mag"][valid][order]
        for xs, ys in split_mlt_track(x, y):
            ax.plot(xs, ys, color=line_color, lw=0.58, alpha=0.32, zorder=1)
        ax.scatter(
            x,
            y,
            c=e,
            cmap=cmap,
            norm=norm,
            marker=marker,
            s=12 if marker == "o" else 14,
            linewidths=0,
            alpha=0.88,
            zorder=2,
        )
        if hemi == "N":
            hi = data["saps_n"] & (data["e_mag"] >= EFIELD_SCREENING_MVM)
        else:
            hi = data["saps_s"] & (data["e_mag"] >= EFIELD_SCREENING_MVM)
        if np.any(hi):
            ax.scatter(
                data[mlt_key][hi],
                data[lat_key][hi],
                facecolors="none",
                edgecolors="black",
                marker=marker,
                s=36 if marker == "o" else 40,
                linewidths=0.70,
                zorder=4,
            )
    ax.set_xlim(0, 24)
    ax.set_ylim(*ylim)
    ax.set_xticks(np.arange(0, 25, 3))
    ax.set_xlabel("Mapped footpoint MLT (h)")
    ax.set_ylabel("CD magnetic latitude (deg)")
    ax.set_title(title, loc="left", fontsize=10.2)
    ax.grid(alpha=0.22)


def add_time_panel(ax, probes):
    colors = {"A": "#7a1688", "B": "#225ea8"}
    for probe, data in probes.items():
        valid = np.isfinite(data["ut"]) & np.isfinite(data["e_mag"])
        ax.plot(data["ut"][valid], data["e_mag"][valid], color=colors[probe], lw=0.92, alpha=0.78, label=f"RBSP-{probe} |E|")
        for row in interval_summary(data, data["saps_any"]):
            ax.axvspan(row["start"], row["end"], color=colors[probe], alpha=0.08, lw=0)
        hi = data["candidate"] & valid
        if np.any(hi):
            ax.scatter(data["ut"][hi], data["e_mag"][hi], color="#d7301f", s=10, linewidths=0, alpha=0.82, zorder=4)
    ax.axhline(EFIELD_SCREENING_MVM, color="black", lw=0.9, ls="--", label="5 mV/m screening level")
    ax.axhline(EFIELD_STRONG_MVM, color="black", lw=0.7, ls=":", label="10 mV/m strong level")
    ax.set_xlim(0, 24)
    ax.set_ylim(0, 18)
    ax.set_xticks(np.arange(0, 25, 3))
    ax.set_xlabel("UT (hour) on 17 Mar 2015")
    ax.set_ylabel("|E| (mV/m)")
    ax.set_title("D. RBSP |E|; shading = mapped footpoint in 15-24 MLT subauroral band", loc="left", fontsize=9.6)
    ax.grid(alpha=0.24)
    ax.legend(loc="upper right", ncol=2, fontsize=7.7, frameon=True)


def make_figure(probes):
    all_e = np.concatenate([data["e_mag"][np.isfinite(data["e_mag"])] for data in probes.values()])
    vmax = max(12.0, min(18.0, float(np.nanpercentile(all_e, 99.2))))
    cmap = "magma_r"
    norm = plt.Normalize(vmin=0.0, vmax=vmax)

    fig, axes = plt.subplots(2, 2, figsize=(13.4, 9.6), dpi=230)
    fig.subplots_adjust(left=0.07, right=0.88, top=0.86, bottom=0.10, hspace=0.34, wspace=0.25)
    add_orbit_panel(axes[0, 0], probes, norm, cmap)
    add_footpoint_panel(axes[0, 1], probes, "N", norm, cmap)
    add_footpoint_panel(axes[1, 0], probes, "S", norm, cmap)
    add_time_panel(axes[1, 1], probes)

    sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    cax = fig.add_axes([0.905, 0.24, 0.022, 0.52])
    cbar = fig.colorbar(sm, cax=cax)
    cbar.set_label("RBSP measured |E| (mV/m)")
    legend_handles = [
        Patch(facecolor="#f2b84b", alpha=0.22, label="N subauroral"),
        Patch(facecolor="#41b6c4", alpha=0.22, label="S subauroral"),
        Patch(facecolor="0.55", alpha=0.12, label="15-24 MLT sector"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="none", markeredgecolor="black", markersize=6, label="|E| >= 5 mV/m in band"),
    ]
    fig.legend(
        legend_handles,
        [h.get_label() for h in legend_handles],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.935),
        ncol=4,
        fontsize=8.2,
        frameon=True,
    )
    fig.suptitle("17 Mar 2015 RBSP magnetospheric mapping and electric-field diagnostic for SAPS screening", y=0.985, fontsize=13.0)
    fig.text(
        0.012,
        0.018,
        "Only magnetospheric satellites are used here. SAPS-candidate points require mapped RBSP footpoint in the 15-24 MLT subauroral band and measured |E| >= 5 mV/m.",
        fontsize=8.0,
        ha="left",
        va="bottom",
    )
    out = ROOT / "rbsp_magnetosphere_mapping_efield_saps_diagnostic.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def summarize_mask(data, mask, label):
    mask = mask & np.isfinite(data["e_mag"])
    if not np.any(mask):
        return f"- RBSP-{data['probe']} {label}: n=0"
    e = data["e_mag"][mask]
    return (
        f"- RBSP-{data['probe']} {label}: n={int(mask.sum())}, "
        f"UT={np.nanmin(data['ut'][mask]):.2f}-{np.nanmax(data['ut'][mask]):.2f}, "
        f"median |E|={np.nanmedian(e):.2f}, p95={np.nanpercentile(e, 95):.2f}, "
        f"max={np.nanmax(e):.2f} mV/m, >=5 mV/m={int(np.sum(e >= EFIELD_SCREENING_MVM))}, "
        f">=10 mV/m={int(np.sum(e >= EFIELD_STRONG_MVM))}"
    )


def write_summary(path, probes):
    lines = [
        "RBSP magnetospheric mapping/electric-field SAPS screening for 17 Mar 2015",
        "",
        "Definition used in this screening figure:",
        f"- subauroral footpoint: centered-dipole |MLAT|={SUBAURORAL_ABS_MLAT[0]:.0f}-{SUBAURORAL_ABS_MLAT[1]:.0f} deg",
        f"- SAPS-relevant MLT sector: {SAPS_MLT[0]:.0f}-{SAPS_MLT[1]:.0f} MLT",
        f"- enhanced electric field marker: |E_spinfit_MGSE| >= {EFIELD_SCREENING_MVM:.1f} mV/m",
        "",
        "Electric-field statistics while mapped footpoints are in the selected regions:",
    ]
    for probe in ["A", "B"]:
        data = probes[probe]
        lines.append(summarize_mask(data, data["sub_n"], "N subauroral"))
        lines.append(summarize_mask(data, data["sub_s"], "S subauroral"))
        lines.append(summarize_mask(data, data["saps_n"], "N subauroral, 15-24 MLT"))
        lines.append(summarize_mask(data, data["saps_s"], "S subauroral, 15-24 MLT"))
    lines.append("")
    lines.append("SAPS-candidate intervals: mapped footpoint in 15-24 MLT subauroral band and |E| >= 5 mV/m")
    any_rows = False
    for probe in ["A", "B"]:
        data = probes[probe]
        rows = interval_summary(data, data["candidate"])
        if not rows:
            lines.append(f"- RBSP-{probe}: none")
            continue
        any_rows = True
        ranked = sorted(rows, key=lambda row: row["max"], reverse=True)
        for i, row in enumerate(ranked[:12], start=1):
            lines.append(
                f"- RBSP-{probe} #{i:02d}: UT {row['start']:.2f}-{row['end']:.2f}, "
                f"n={row['n']}, median={row['median']:.2f}, p95={row['p95']:.2f}, max={row['max']:.2f} mV/m"
            )
        if len(ranked) > 12:
            lines.append(f"- RBSP-{probe}: {len(ranked) - 12} additional shorter/lower-|E| intervals omitted")
    if not any_rows:
        lines.append("- No intervals met the screening criterion.")
    lines.append("")
    lines.append(
        "Caveat: This is a screening diagnostic based only on RBSP magnetospheric EFW and MagEphem footpoint mapping. "
        "It does not use ionospheric-satellite drift or GUVI data."
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_candidate_csv(path, probes):
    fieldnames = ["probe", "ut_start", "ut_end", "n_points", "median_e_mvm", "p95_e_mvm", "max_e_mvm"]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for probe in ["A", "B"]:
            rows = interval_summary(probes[probe], probes[probe]["candidate"])
            for row in sorted(rows, key=lambda item: (item["start"], item["end"])):
                writer.writerow(
                    {
                        "probe": f"RBSP-{probe}",
                        "ut_start": f"{row['start']:.4f}",
                        "ut_end": f"{row['end']:.4f}",
                        "n_points": row["n"],
                        "median_e_mvm": f"{row['median']:.4f}",
                        "p95_e_mvm": f"{row['p95']:.4f}",
                        "max_e_mvm": f"{row['max']:.4f}",
                    }
                )


def main():
    probes = {probe: read_rbsp_probe(probe) for probe in ["A", "B"]}
    fig_path = make_figure(probes)
    summary_path = ROOT / "rbsp_magnetosphere_mapping_efield_saps_diagnostic_summary.txt"
    csv_path = ROOT / "rbsp_magnetosphere_mapping_efield_saps_candidate_intervals.csv"
    write_summary(summary_path, probes)
    write_candidate_csv(csv_path, probes)
    print(fig_path)
    print(summary_path)
    print(csv_path)


if __name__ == "__main__":
    main()

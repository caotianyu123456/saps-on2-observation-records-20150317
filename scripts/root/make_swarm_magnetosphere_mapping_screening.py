from pathlib import Path

import cdflib
import matplotlib.pyplot as plt
import netCDF4
import numpy as np

from make_guvi_dmsp_mlt_candidate import (
    DIPOLE_POLE_LAT,
    DIPOLE_POLE_LON,
    GUVI_FILES,
    centered_dipole_coords,
    read_dmsp,
)


ROOT = Path(__file__).resolve().parent
RE_KM = 6371.2

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

THEMIS_PROBES = ["tha", "thd", "the"]


def cdf_time_to_unix_seconds(values):
    dt64 = cdflib.cdfepoch.to_datetime(values)
    return np.asarray(dt64).astype("datetime64[ns]").astype("int64") / 1e9


def unix_to_ut_hour(values):
    return ((values - 1426550400.0) / 3600.0) % 24.0


def read_guvi_raw(path):
    with netCDF4.Dataset(path) as ds:
        doy = np.asarray(ds.variables["FRACTIONAL_DOY"][:], dtype=float)
        on2 = np.asarray(ds.variables["ON2"][:], dtype=float)
        lat = np.asarray(ds.variables["LATITUDE"][:], dtype=float)
        lon = np.asarray(ds.variables["LONGITUDE"][:], dtype=float)
    valid = np.isfinite(on2) & (np.abs(on2) < 1e20) & np.isfinite(lat) & np.isfinite(lon)
    mlat, mlt = centered_dipole_coords(lat[valid], lon[valid], doy[valid])
    return {"mlat": mlat, "mlt": mlt, "on2": on2[valid]}


def median_grid(data, mlt_edges, mlat_edges, min_count=3):
    out = np.full((len(mlat_edges) - 1, len(mlt_edges) - 1), np.nan)
    count = np.zeros_like(out, dtype=int)
    for iy in range(len(mlat_edges) - 1):
        y0, y1 = mlat_edges[iy], mlat_edges[iy + 1]
        ymask = (data["mlat"] >= y0) & (data["mlat"] < y1)
        for ix in range(len(mlt_edges) - 1):
            x0, x1 = mlt_edges[ix], mlt_edges[ix + 1]
            mask = ymask & (data["mlt"] >= x0) & (data["mlt"] < x1)
            count[iy, ix] = int(mask.sum())
            if count[iy, ix] >= min_count:
                out[iy, ix] = np.nanmedian(data["on2"][mask])
    return out, count


def sector_mask(mlt, mlat, hemi, mlt_range):
    if hemi == "N":
        lat_mask = (mlat >= 48.0) & (mlat <= 70.0)
    else:
        lat_mask = (mlat >= -70.0) & (mlat <= -48.0)
    return lat_mask & (mlt >= mlt_range[0]) & (mlt <= mlt_range[1])


def summarize_quantity(name, hemi, mlt_range, mlt, mlat, value, ut=None, units=""):
    mask = sector_mask(mlt, mlat, hemi, mlt_range) & np.isfinite(value)
    if not np.any(mask):
        return {
            "name": name,
            "hemi": hemi,
            "mlt_range": f"{mlt_range[0]:.0f}-{mlt_range[1]:.0f}",
            "n": 0,
            "median": np.nan,
            "p95": np.nan,
            "max": np.nan,
            "ut": "",
            "mlt": "",
            "units": units,
        }
    selected = value[mask]
    row = {
        "name": name,
        "hemi": hemi,
        "mlt_range": f"{mlt_range[0]:.0f}-{mlt_range[1]:.0f}",
        "n": int(mask.sum()),
        "median": float(np.nanmedian(selected)),
        "p95": float(np.nanpercentile(selected, 95)),
        "max": float(np.nanmax(selected)),
        "ut": "",
        "mlt": f"{np.nanmin(mlt[mask]):.2f}-{np.nanmax(mlt[mask]):.2f}",
        "units": units,
    }
    if ut is not None:
        row["ut"] = f"{np.nanmin(ut[mask]):.2f}-{np.nanmax(ut[mask]):.2f}"
    return row


def read_rbsp_mapped():
    rows = []
    for probe, paths in RBSP_FILES.items():
        if not paths["efw"].exists() or not paths["mage"].exists():
            continue
        efw = cdflib.CDF(str(paths["efw"]))
        mage = cdflib.CDF(str(paths["mage"]))

        e_time = cdf_time_to_unix_seconds(efw.varget("epoch"))
        efield = np.asarray(efw.varget("efield_spinfit_mgse"), dtype=float)
        efield[np.abs(efield) > 1e20] = np.nan
        finite_components = np.isfinite(efield)
        e_mag = np.sqrt(np.nansum(np.where(finite_components, efield, 0.0) ** 2, axis=1))
        e_mag[finite_components.sum(axis=1) == 0] = np.nan
        good = np.isfinite(e_time) & np.isfinite(e_mag)
        order = np.argsort(e_time[good])
        e_time_good = e_time[good][order]
        e_mag_good = e_mag[good][order]

        m_time = cdf_time_to_unix_seconds(mage.varget("Epoch"))
        e_on_mage = np.interp(m_time, e_time_good, e_mag_good, left=np.nan, right=np.nan)
        for hemi, lat_var, mlt_var, geo_var in [
            ("N", "Pfn_CD_MLAT", "Pfn_CD_MLT", "Pfn_geod_LatLon"),
            ("S", "Pfs_CD_MLAT", "Pfs_CD_MLT", "Pfs_geod_LatLon"),
        ]:
            mlat = np.asarray(mage.varget(lat_var), dtype=float)
            mlt = np.asarray(mage.varget(mlt_var), dtype=float) % 24.0
            geo = np.asarray(mage.varget(geo_var), dtype=float)
            valid = (
                np.isfinite(mlat)
                & np.isfinite(mlt)
                & np.isfinite(e_on_mage)
                & (np.abs(mlat) < 90.0)
                & (e_on_mage < 100.0)
            )
            rows.append(
                {
                    "source": f"RBSP-{probe}",
                    "hemi": hemi,
                    "time": m_time[valid],
                    "ut": unix_to_ut_hour(m_time[valid]),
                    "mlt": mlt[valid],
                    "mlat": mlat[valid],
                    "glat": geo[valid, 0],
                    "glon": geo[valid, 1],
                    "value": e_on_mage[valid],
                }
            )
    return rows


def read_themis_mapped():
    rows = []
    for probe in THEMIS_PROBES:
        state_path = ROOT / f"themis_data/{probe}/l1/state/2015/{probe}_l1_state_20150317.cdf"
        mom_path = ROOT / f"themis_data/{probe}/l2/mom/2015/{probe}_l2_mom_20150317_v01.cdf"
        if not state_path.exists() or not mom_path.exists():
            continue
        state = cdflib.CDF(str(state_path))
        mom = cdflib.CDF(str(mom_path))
        state_time = np.asarray(state.varget(f"{probe}_state_time"), dtype=float)
        pos_gsm = np.asarray(state.varget(f"{probe}_pos_gsm"), dtype=float) / RE_KM
        mom_time = np.asarray(mom.varget(f"{probe}_peim_time"), dtype=float)
        vel = np.asarray(mom.varget(f"{probe}_peim_velocity_gsm"), dtype=float)
        vel[np.abs(vel) > 1e20] = np.nan
        speed = np.linalg.norm(vel, axis=1)
        good_speed = np.isfinite(mom_time) & np.isfinite(speed) & (speed < 2000.0)
        speed_on_state = np.interp(
            state_time,
            mom_time[good_speed],
            speed[good_speed],
            left=np.nan,
            right=np.nan,
        )

        x, y, z = pos_gsm[:, 0], pos_gsm[:, 1], pos_gsm[:, 2]
        r = np.linalg.norm(pos_gsm, axis=1)
        dipole_lat = np.arctan2(z, np.hypot(x, y))
        cos2 = np.cos(dipole_lat) ** 2
        lshell = r / np.maximum(cos2, 1e-6)
        foot_abs = np.rad2deg(np.arccos(np.sqrt(np.clip(1.0 / lshell, 0.0, 1.0))))
        mlt = (12.0 + np.rad2deg(np.arctan2(y, x)) / 15.0) % 24.0
        valid = np.isfinite(foot_abs) & np.isfinite(mlt) & np.isfinite(speed_on_state) & (lshell >= 2.0)

        for hemi, sign in [("N", 1.0), ("S", -1.0)]:
            rows.append(
                {
                    "source": probe.upper(),
                    "hemi": hemi,
                    "time": state_time[valid],
                    "ut": unix_to_ut_hour(state_time[valid]),
                    "mlt": mlt[valid],
                    "mlat": sign * foot_abs[valid],
                    "value": speed_on_state[valid],
                }
            )
    return rows


def stack_records(records, source_filter=None, hemi=None):
    selected = []
    for rec in records:
        if source_filter is not None and not rec["source"].startswith(source_filter):
            continue
        if hemi is not None and rec["hemi"] != hemi:
            continue
        selected.append(rec)
    if not selected:
        return None
    keys = ["mlt", "mlat", "value", "ut"]
    return {key: np.concatenate([rec[key] for rec in selected]) for key in keys}


def summarize_guvi_sector(data16, data17, hemi, mlt_range):
    mask16 = sector_mask(data16["mlt"], data16["mlat"], hemi, mlt_range)
    mask17 = sector_mask(data17["mlt"], data17["mlat"], hemi, mlt_range)
    med16 = np.nanmedian(data16["on2"][mask16]) if np.any(mask16) else np.nan
    med17 = np.nanmedian(data17["on2"][mask17]) if np.any(mask17) else np.nan
    return {
        "name": "GUVI O/N2",
        "hemi": hemi,
        "mlt_range": f"{mlt_range[0]:.0f}-{mlt_range[1]:.0f}",
        "n16": int(mask16.sum()),
        "n17": int(mask17.sum()),
        "median16": med16,
        "median17": med17,
        "delta": med17 - med16 if np.isfinite(med16) and np.isfinite(med17) else np.nan,
    }


def format_summary(guvi_rows, quantity_rows, swarm_note):
    lines = []
    lines.append("Screening summary for 17 Mar 2015")
    lines.append("")
    lines.append("GUVI O/N2 sector medians, centered-dipole coordinates:")
    for row in guvi_rows:
        lines.append(
            f"- {row['hemi']} MLT {row['mlt_range']}: n16={row['n16']}, n17={row['n17']}, "
            f"med16={row['median16']:.3f}, med17={row['median17']:.3f}, delta={row['delta']:.3f}"
        )
    lines.append("")
    lines.append("Mapped/low-orbit flow or electric-field diagnostics:")
    for row in quantity_rows:
        if row["n"] == 0:
            lines.append(f"- {row['name']} {row['hemi']} MLT {row['mlt_range']}: n=0")
            continue
        lines.append(
            f"- {row['name']} {row['hemi']} MLT {row['mlt_range']}: n={row['n']}, "
            f"UT={row['ut']}, MLT={row['mlt']}, median={row['median']:.2f}, "
            f"p95={row['p95']:.2f}, max={row['max']:.2f} {row['units']}"
        )
    lines.append("")
    lines.append(swarm_note)
    lines.append("")
    lines.append(
        "Caveat: GUVI and DMSP coordinates use a centered-dipole screening conversion; "
        "THEMIS mapping is an approximate dipole conjugate-footpoint estimate; RBSP uses MagEphem footpoints."
    )
    return "\n".join(lines)


def plot_screening(data16, data17, dmsp, rbsp_records, themis_records):
    mlt_edges = np.arange(10.0, 24.01, 0.5)
    fig, axes = plt.subplots(2, 1, figsize=(11.2, 9.0), dpi=220, sharex=True)

    for ax, hemi, mlat_edges in [
        (axes[0], "N", np.arange(45.0, 75.01, 1.5)),
        (axes[1], "S", np.arange(-75.0, -44.99, 1.5)),
    ]:
        med16, _ = median_grid(data16, mlt_edges, mlat_edges)
        med17, _ = median_grid(data17, mlt_edges, mlat_edges)
        delta = med17 - med16
        mesh = ax.pcolormesh(
            mlt_edges,
            mlat_edges,
            delta,
            cmap="RdBu_r",
            vmin=-0.8,
            vmax=0.8,
            shading="auto",
            alpha=0.88,
        )
        ax.axvspan(12, 18, color="none", ec="#d62728", lw=2.0)
        ax.axvspan(18, 24, color="none", ec="#d62728", lw=1.8, ls="--")

        dmsp_mask = (
            (dmsp["cd_mlt"] >= 10.0)
            & (dmsp["cd_mlt"] <= 24.0)
            & (dmsp["cd_mlat"] >= mlat_edges[0])
            & (dmsp["cd_mlat"] <= mlat_edges[-1])
        )
        for sat, color in [("F17", "#7a1688"), ("F18", "#5e3c99")]:
            sat_mask = dmsp_mask & (dmsp["satellite"] == sat)
            if np.any(sat_mask):
                order = np.argsort(dmsp["ut"][sat_mask])
                ax.scatter(
                    dmsp["cd_mlt"][sat_mask][order],
                    dmsp["cd_mlat"][sat_mask][order],
                    s=5,
                    color=color,
                    alpha=0.42,
                    linewidths=0,
                    label=f"DMSP {sat}" if hemi == "N" else None,
                    zorder=4,
                )

        rbsp = stack_records(rbsp_records, source_filter="RBSP", hemi=hemi)
        if rbsp is not None:
            mask = (
                (rbsp["mlt"] >= 10.0)
                & (rbsp["mlt"] <= 24.0)
                & (rbsp["mlat"] >= mlat_edges[0])
                & (rbsp["mlat"] <= mlat_edges[-1])
            )
            if np.any(mask):
                sizes = 7.0 + np.clip(rbsp["value"][mask], 0, 25) * 2.2
                ax.scatter(
                    rbsp["mlt"][mask],
                    rbsp["mlat"][mask],
                    s=sizes,
                    marker="o",
                    facecolors="#ffb000",
                    edgecolors="black",
                    linewidths=0.25,
                    alpha=0.72,
                    label="RBSP footpoint |E|" if hemi == "N" else None,
                    zorder=5,
                )

        themis = stack_records(themis_records, hemi=hemi)
        if themis is not None:
            mask = (
                (themis["mlt"] >= 10.0)
                & (themis["mlt"] <= 24.0)
                & (themis["mlat"] >= mlat_edges[0])
                & (themis["mlat"] <= mlat_edges[-1])
            )
            if np.any(mask):
                sizes = 8.0 + np.clip(themis["value"][mask], 0, 700) * 0.045
                ax.scatter(
                    themis["mlt"][mask],
                    themis["mlat"][mask],
                    s=sizes,
                    marker="^",
                    facecolors="#1b9e77",
                    edgecolors="black",
                    linewidths=0.2,
                    alpha=0.68,
                    label="THEMIS mapped |Vi|" if hemi == "N" else None,
                    zorder=6,
                )

        ax.set_xlim(10, 24)
        ax.set_ylim(mlat_edges[0], mlat_edges[-1])
        ax.grid(alpha=0.23)
        ax.set_ylabel(f"{hemi} CD magnetic latitude (deg)")
        ax.text(
            12.1,
            mlat_edges[-1] - (2.0 if hemi == "N" else -2.0),
            "12-18 MLT",
            color="#d62728",
            fontsize=8.5,
            va="top" if hemi == "N" else "bottom",
        )
        ax.text(
            18.1,
            mlat_edges[-1] - (2.0 if hemi == "N" else -2.0),
            "18-24 MLT",
            color="#d62728",
            fontsize=8.5,
            va="top" if hemi == "N" else "bottom",
        )

    axes[0].legend(loc="upper left", ncol=2, fontsize=8.3, frameon=True)
    axes[1].set_xlabel("Magnetic local time (hour)")
    cbar = fig.colorbar(mesh, ax=axes, pad=0.015, shrink=0.86)
    cbar.set_label("GUVI Delta O/N2 (17 Mar minus 16 Mar)")
    fig.suptitle(
        "Screening: GUVI O/N2 anomaly with DMSP, RBSP mapped footpoints, and THEMIS mapped footpoints",
        y=0.985,
        fontsize=12.6,
    )
    fig.text(
        0.012,
        0.016,
        "Swarm EFI/TIE ion drift was not plotted because no local Swarm drift CDF is present and VirES TCT02/TIE access requires an account token. "
        "RBSP marker size: |E| in mV/m. THEMIS marker size: ion bulk-speed magnitude in km/s.",
        fontsize=8.0,
        ha="left",
        va="bottom",
    )
    fig.tight_layout(rect=[0, 0.045, 0.93, 0.955])
    out = ROOT / "swarm_magnetosphere_mapping_screening.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def main():
    data16 = read_guvi_raw(GUVI_FILES["16 Mar"])
    data17 = read_guvi_raw(GUVI_FILES["17 Mar"])
    dmsp = read_dmsp()
    rbsp_records = read_rbsp_mapped()
    themis_records = read_themis_mapped()

    guvi_rows = []
    quantity_rows = []
    for hemi in ["N", "S"]:
        for mlt_range in [(12.0, 18.0), (18.0, 24.0)]:
            guvi_rows.append(summarize_guvi_sector(data16, data17, hemi, mlt_range))
            quantity_rows.append(
                summarize_quantity(
                    "DMSP |Vi|",
                    hemi,
                    mlt_range,
                    dmsp["cd_mlt"],
                    dmsp["cd_mlat"],
                    np.abs(dmsp["horizontal_ion_drift_mps"]) / 1000.0,
                    ut=dmsp["ut"],
                    units="km/s",
                )
            )
            rbsp = stack_records(rbsp_records, source_filter="RBSP", hemi=hemi)
            if rbsp is not None:
                quantity_rows.append(
                    summarize_quantity(
                        "RBSP mapped |E|",
                        hemi,
                        mlt_range,
                        rbsp["mlt"],
                        rbsp["mlat"],
                        rbsp["value"],
                        ut=rbsp["ut"],
                        units="mV/m",
                    )
                )
            themis = stack_records(themis_records, hemi=hemi)
            if themis is not None:
                quantity_rows.append(
                    summarize_quantity(
                        "THEMIS mapped |Vi|",
                        hemi,
                        mlt_range,
                        themis["mlt"],
                        themis["mlat"],
                        themis["value"],
                        ut=themis["ut"],
                        units="km/s",
                    )
                )

    swarm_files = list(ROOT.glob("**/*SW*EFI*T*.cdf")) + list(ROOT.glob("**/*swarm*drift*.cdf"))
    if swarm_files:
        swarm_note = f"Swarm note: found {len(swarm_files)} possible local files, but no parser was applied in this screening run."
    else:
        swarm_note = (
            "Swarm note: no local Swarm EFI/TCT02/TIE ion-drift CDF was found. "
            "VirES lists the needed EFI/TIE variables, but data download requires a VirES token/account, so this branch is currently blocked."
        )

    out = plot_screening(data16, data17, dmsp, rbsp_records, themis_records)
    summary = format_summary(guvi_rows, quantity_rows, swarm_note)
    summary_path = ROOT / "swarm_magnetosphere_mapping_screening_summary.txt"
    summary_path.write_text(summary, encoding="utf-8")
    print(summary)
    print("")
    print(out)
    print(summary_path)


if __name__ == "__main__":
    main()

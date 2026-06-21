import csv
from pathlib import Path

import matplotlib.pyplot as plt
import netCDF4
import numpy as np


ROOT = Path(__file__).resolve().parent
GUVI_FILES = {
    "16 Mar": ROOT / "timed_guvi_l3-on2_2015075_Av0100r000.nc",
    "17 Mar": ROOT / "timed_guvi_l3-on2_2015076_Av0100r000.nc",
}
DMSP_FILES = [
    ROOT / "dmsp_f17_ssies_20150317_parsed.csv",
    ROOT / "dmsp_f18_ssies_20150317_parsed.csv",
]

# Centered-dipole north pole, approximate for 2015. This is for screening.
DIPOLE_POLE_LAT = 80.37
DIPOLE_POLE_LON = -72.62


def unit_vector(lat, lon):
    lat = np.deg2rad(lat)
    lon = np.deg2rad(lon)
    return np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], axis=0)


M_AXIS = unit_vector(DIPOLE_POLE_LAT, DIPOLE_POLE_LON).reshape(3)
REF = np.array([1.0, 0.0, 0.0])
EX = REF - np.dot(REF, M_AXIS) * M_AXIS
EX = EX / np.linalg.norm(EX)
EY = np.cross(M_AXIS, EX)


def subsolar_lat_lon(doy):
    frac_hour = (doy % 1.0) * 24.0
    day = np.floor(doy)
    gamma = 2 * np.pi / 365.0 * (day - 1 + (frac_hour - 12) / 24.0)
    eqtime = 229.18 * (
        0.000075
        + 0.001868 * np.cos(gamma)
        - 0.032077 * np.sin(gamma)
        - 0.014615 * np.cos(2 * gamma)
        - 0.040849 * np.sin(2 * gamma)
    )
    decl = (
        0.006918
        - 0.399912 * np.cos(gamma)
        + 0.070257 * np.sin(gamma)
        - 0.006758 * np.cos(2 * gamma)
        + 0.000907 * np.sin(2 * gamma)
        - 0.002697 * np.cos(3 * gamma)
        + 0.00148 * np.sin(3 * gamma)
    )
    lon = (720.0 - frac_hour * 60.0 - eqtime) / 4.0
    lon = ((lon + 180.0) % 360.0) - 180.0
    return np.rad2deg(decl), lon


def centered_dipole_coords(lat, lon, doy):
    r = unit_vector(lat, lon)
    mlat = np.rad2deg(np.arcsin(np.clip(np.einsum("i,ij->j", M_AXIS, r), -1, 1)))
    phi = np.rad2deg(np.arctan2(np.einsum("i,ij->j", EY, r), np.einsum("i,ij->j", EX, r)))
    ss_lat, ss_lon = subsolar_lat_lon(doy)
    rs = unit_vector(ss_lat, ss_lon)
    ss_phi = np.rad2deg(np.arctan2(np.einsum("i,ij->j", EY, rs), np.einsum("i,ij->j", EX, rs)))
    mlt = (12.0 + (phi - ss_phi) / 15.0) % 24.0
    return mlat, mlt


def read_guvi(path):
    ds = netCDF4.Dataset(path)
    doy = np.asarray(ds.variables["FRACTIONAL_DOY"][:], dtype=float)
    on2 = np.asarray(ds.variables["ON2"][:], dtype=float)
    lat = np.asarray(ds.variables["LATITUDE"][:], dtype=float)
    lon = np.asarray(ds.variables["LONGITUDE"][:], dtype=float)
    ds.close()
    valid = np.isfinite(on2) & (np.abs(on2) < 1e20) & np.isfinite(lat) & np.isfinite(lon)
    mlat, mlt = centered_dipole_coords(lat[valid], lon[valid], doy[valid])
    return {"mlat": mlat, "mlt": mlt, "on2": on2[valid]}


def read_dmsp():
    rows = []
    for path in DMSP_FILES:
        with open(path, newline="") as handle:
            for row in csv.DictReader(handle):
                parsed = {"satellite": row["satellite"], "time_iso": row["time_iso"]}
                for key, value in row.items():
                    if key not in parsed:
                        parsed[key] = float(value)
                rows.append(parsed)
    cols = {}
    for key in rows[0]:
        if key in {"satellite", "time_iso"}:
            cols[key] = np.asarray([row[key] for row in rows])
        else:
            cols[key] = np.asarray([row[key] for row in rows], dtype=float)
    doy = 76.0 + cols["ut"] / 24.0
    cd_mlat, cd_mlt = centered_dipole_coords(cols["glat"], cols["glon"], doy)
    cols["cd_mlat"] = cd_mlat
    cols["cd_mlt"] = cd_mlt
    return cols


def add_speed_arrows(ax, cols, idx, color="#7a1688"):
    x = cols["cd_mlt"][idx]
    y = cols["cd_mlat"][idx]
    order = np.argsort(cols["ut"][idx])
    idx = idx[order]
    x = cols["cd_mlt"][idx]
    y = cols["cd_mlat"][idx]
    ax.plot(x, y, color=color, lw=1.9, alpha=0.92, zorder=5)
    xy = ax.transData.transform(np.column_stack([x, y]))
    tangent = np.gradient(xy, axis=0)
    norm = np.hypot(tangent[:, 0], tangent[:, 1])
    ok = norm > 0
    tangent[ok] = tangent[ok] / norm[ok, None]
    normal = np.column_stack([-tangent[:, 1], tangent[:, 0]])
    normal[normal[:, 0] < 0] *= -1
    positions = np.arange(8, len(idx) - 8, 26)
    if len(positions) > 24:
        positions = positions[np.linspace(0, len(positions) - 1, 24, dtype=int)]
    for pos in positions:
        drift = cols["horizontal_ion_drift_mps"][idx[pos]]
        length_px = min(abs(drift), 3000.0) / 1000.0 * 18.0
        if length_px < 2:
            continue
        start = ax.transData.transform((x[pos], y[pos]))
        end = start + normal[pos] * length_px
        end_xy = ax.transData.inverted().transform(end)
        ax.annotate(
            "",
            xy=end_xy,
            xytext=(x[pos], y[pos]),
            arrowprops=dict(arrowstyle="-|>", color=color, lw=0.35, mutation_scale=3.0, shrinkA=0, shrinkB=0),
            zorder=7,
        )


def lat_profile(data, mlt_range=(12, 18), bins=np.arange(-70, -47.9, 4)):
    centers = (bins[:-1] + bins[1:]) / 2
    med = np.full(len(centers), np.nan)
    count = np.zeros(len(centers), dtype=int)
    for i in range(len(centers)):
        m = (
            (data["mlt"] >= mlt_range[0])
            & (data["mlt"] <= mlt_range[1])
            & (data["mlat"] >= bins[i])
            & (data["mlat"] < bins[i + 1])
        )
        count[i] = int(m.sum())
        if count[i]:
            med[i] = np.nanmedian(data["on2"][m])
    return centers, med, count


def main():
    guvi16 = read_guvi(GUVI_FILES["16 Mar"])
    guvi17 = read_guvi(GUVI_FILES["17 Mar"])
    cols = read_dmsp()

    guvi_mask16 = (guvi16["mlat"] >= -70) & (guvi16["mlat"] <= -48) & (guvi16["mlt"] >= 12) & (guvi16["mlt"] <= 18)
    guvi_mask17 = (guvi17["mlat"] >= -70) & (guvi17["mlat"] <= -48) & (guvi17["mlt"] >= 12) & (guvi17["mlt"] <= 18)

    dmsp_mask = (
        (cols["satellite"] == "F17")
        & (cols["cd_mlat"] >= -70)
        & (cols["cd_mlat"] <= -48)
        & (cols["cd_mlt"] >= 12)
        & (cols["cd_mlt"] <= 18)
    )
    dmsp_idx = np.where(dmsp_mask)[0]
    drift = cols["horizontal_ion_drift_mps"][dmsp_idx]

    print(
        "GUVI candidate sector MLAT -70 to -48, MLT 12-18: "
        f"16 Mar n={int(guvi_mask16.sum())}, median={np.nanmedian(guvi16['on2'][guvi_mask16]):.3f}; "
        f"17 Mar n={int(guvi_mask17.sum())}, median={np.nanmedian(guvi17['on2'][guvi_mask17]):.3f}"
    )
    print(
        "DMSP F17 same centered-dipole sector: "
        f"n={len(dmsp_idx)}, UT={cols['ut'][dmsp_idx].min():.2f}-{cols['ut'][dmsp_idx].max():.2f}, "
        f"MLT={cols['cd_mlt'][dmsp_idx].min():.2f}-{cols['cd_mlt'][dmsp_idx].max():.2f}, "
        f"median |Vi|={np.nanmedian(np.abs(drift)):.0f} m/s, max |Vi|={np.nanmax(np.abs(drift)):.0f} m/s"
    )

    fig, axes = plt.subplots(3, 1, figsize=(10.2, 11.0), dpi=220, gridspec_kw={"height_ratios": [1.6, 1.6, 1.0]})
    for ax, data, label, mask in [
        (axes[0], guvi16, "16 Mar 2015", guvi_mask16),
        (axes[1], guvi17, "17 Mar 2015", guvi_mask17),
    ]:
        region = (data["mlat"] >= -75) & (data["mlat"] <= -45) & (data["mlt"] >= 11.5) & (data["mlt"] <= 18.5)
        sc = ax.scatter(data["mlt"][region], data["mlat"][region], c=data["on2"][region], s=12, cmap="viridis", vmin=0, vmax=1.1, linewidths=0)
        ax.plot([12, 18, 18, 12, 12], [-70, -70, -48, -48, -70], color="#d62728", lw=2.0)
        ax.text(12.1, -49.5, f"candidate sector\nn={int(mask.sum())}\nmedian={np.nanmedian(data['on2'][mask]):.3f}", color="#8b0000", fontsize=8.4, va="top")
        if label.startswith("17"):
            add_speed_arrows(ax, cols, dmsp_idx)
            ax.text(
                17.02,
                -50.0,
                f"F17 DMSP\nUT {cols['ut'][dmsp_idx].min():.2f}-{cols['ut'][dmsp_idx].max():.2f}\nmax |Vi|={np.nanmax(np.abs(drift))/1000:.1f} km/s",
                color="#7a1688",
                fontsize=8.0,
                ha="left",
                va="top",
                bbox=dict(fc="white", ec="none", alpha=0.74, pad=1.4),
                zorder=9,
            )
        cbar = fig.colorbar(sc, ax=ax, pad=0.012)
        cbar.set_label("GUVI O/N2")
        ax.set_xlim(11.5, 18.5)
        ax.set_ylim(-75, -45)
        ax.set_ylabel("Centered-dipole magnetic latitude (deg)")
        ax.set_title(f"{label}: GUVI raw O/N2 in approximate MLT/MLAT")
        ax.grid(alpha=0.22)

    centers, med16, n16 = lat_profile(guvi16)
    _, med17, n17 = lat_profile(guvi17)
    ax = axes[2]
    ax.plot(centers, med16, "o-", label="16 Mar", color="#4c78a8")
    ax.plot(centers, med17, "o-", label="17 Mar", color="#f58518")
    for x, y16, y17, a, b in zip(centers, med16, med17, n16, n17):
        if np.isfinite(y16) and np.isfinite(y17):
            ax.text(x, y17 + 0.045, f"{y17-y16:+.2f}", ha="center", va="bottom", fontsize=8)
            ax.text(x, 0.06, f"n={a}/{b}", ha="center", va="bottom", fontsize=7.5, color="0.35")
    ax.set_xlim(-71, -47)
    ax.set_ylim(0, 1.1)
    ax.set_xlabel("Centered-dipole magnetic latitude bin center (deg)")
    ax.set_ylabel("Median O/N2")
    ax.set_title("GUVI O/N2 latitudinal medians in MLT 12-18; labels show 17 Mar minus 16 Mar")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper right")

    fig.suptitle("Candidate Southern-Hemisphere GUVI O/N2 Depletion and DMSP Drift in MLT Coordinates", y=0.988, fontsize=13.4)
    fig.text(
        0.015,
        0.012,
        "Screening plot: GUVI MLT/MLAT is computed with a centered-dipole approximation. "
        "A formal paper figure should recompute these coordinates with AACGM/Apex.",
        ha="left",
        va="bottom",
        fontsize=8.2,
    )
    fig.tight_layout(rect=[0, 0.035, 1, 0.962])
    out = ROOT / "guvi_dmsp_mlt_candidate_southern.png"
    fig.savefig(out)
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    main()

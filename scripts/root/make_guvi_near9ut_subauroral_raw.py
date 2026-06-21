from pathlib import Path

import matplotlib.pyplot as plt
import netCDF4
import numpy as np


ROOT = Path(__file__).resolve().parent
FILES = {
    "16 Mar 2015": ROOT / "timed_guvi_l3-on2_2015075_Av0100r000.nc",
    "17 Mar 2015": ROOT / "timed_guvi_l3-on2_2015076_Av0100r000.nc",
}
UT_MIN = 7.0
UT_MAX = 11.0


def read_raw(path):
    ds = netCDF4.Dataset(path)
    doy = np.asarray(ds.variables["FRACTIONAL_DOY"][:], dtype=float)
    on2 = np.asarray(ds.variables["ON2"][:], dtype=float)
    lat = np.asarray(ds.variables["LATITUDE"][:], dtype=float)
    lon = np.asarray(ds.variables["LONGITUDE"][:], dtype=float)
    sza = np.asarray(ds.variables["SOLAR ZENITH ANGLE"][:], dtype=float)
    orbit = np.asarray(ds.variables["ORBIT"][:], dtype=float)
    ds.close()

    ut = (doy % 1.0) * 24.0
    lt = (ut + lon / 15.0) % 24.0
    valid = np.isfinite(on2) & (np.abs(on2) < 1e20) & np.isfinite(lat) & np.isfinite(lon)
    return {"ut": ut, "lt": lt, "lat": lat, "lon": lon, "on2": on2, "sza": sza, "orbit": orbit, "valid": valid}


def mask_subauroral_near9(raw):
    return raw["valid"] & (raw["ut"] >= UT_MIN) & (raw["ut"] <= UT_MAX) & (raw["lat"] >= 40) & (raw["lat"] <= 65)


def lat_profile(raw, mask, bins):
    med = np.full(len(bins) - 1, np.nan)
    p25 = np.full(len(bins) - 1, np.nan)
    p75 = np.full(len(bins) - 1, np.nan)
    count = np.zeros(len(bins) - 1, dtype=int)
    for i in range(len(bins) - 1):
        m = mask & (raw["lat"] >= bins[i]) & (raw["lat"] < bins[i + 1])
        count[i] = int(m.sum())
        if count[i]:
            med[i] = np.nanmedian(raw["on2"][m])
            p25[i] = np.nanpercentile(raw["on2"][m], 25)
            p75[i] = np.nanpercentile(raw["on2"][m], 75)
    return med, p25, p75, count


def main():
    data = {label: read_raw(path) for label, path in FILES.items()}
    masks = {label: mask_subauroral_near9(raw) for label, raw in data.items()}

    for label, raw in data.items():
        m = masks[label]
        print(label)
        print(f"  n = {int(m.sum())}")
        print(
            "  UT = {:.2f}-{:.2f}, observed LT = {:.2f}-{:.2f}, lat = {:.1f}-{:.1f}, "
            "lon = {:.1f}-{:.1f}, median O/N2 = {:.3f}".format(
                np.nanmin(raw["ut"][m]),
                np.nanmax(raw["ut"][m]),
                np.nanmin(raw["lt"][m]),
                np.nanmax(raw["lt"][m]),
                np.nanmin(raw["lat"][m]),
                np.nanmax(raw["lat"][m]),
                np.nanmin(raw["lon"][m]),
                np.nanmax(raw["lon"][m]),
                np.nanmedian(raw["on2"][m]),
            )
        )
        print(f"  orbits = {sorted(set(raw['orbit'][m].astype(int).tolist()))}")

    bins = np.arange(40, 66, 5)
    centers = (bins[:-1] + bins[1:]) / 2.0
    profiles = {label: lat_profile(raw, masks[label], bins) for label, raw in data.items()}
    delta = profiles["17 Mar 2015"][0] - profiles["16 Mar 2015"][0]

    fig, axes = plt.subplots(3, 1, figsize=(9.0, 9.2), dpi=220, sharex=False)
    for ax, label in zip(axes[:2], ["16 Mar 2015", "17 Mar 2015"]):
        raw = data[label]
        m = masks[label]
        sc = ax.scatter(raw["lt"][m], raw["lat"][m], c=raw["on2"][m], s=18, cmap="viridis", vmin=0, vmax=1.1)
        ax.set_xlim(6.8, 9.5)
        ax.set_ylim(39, 66)
        ax.grid(alpha=0.25)
        ax.set_ylabel("Geographic latitude (deg)")
        ax.set_title(
            f"{label}: GUVI raw O/N2 observations during {UT_MIN:.0f}-{UT_MAX:.0f} UT, subauroral latitudes\n"
            f"n={int(m.sum())}, UT {raw['ut'][m].min():.2f}-{raw['ut'][m].max():.2f}, "
            f"observed LT {raw['lt'][m].min():.2f}-{raw['lt'][m].max():.2f}"
        )
        cbar = fig.colorbar(sc, ax=ax, pad=0.012)
        cbar.set_label("O/N2")

    ax = axes[2]
    med16, p2516, p7516, n16 = profiles["16 Mar 2015"]
    med17, p2517, p7517, n17 = profiles["17 Mar 2015"]
    ax.plot(centers, med16, "o-", color="#4c78a8", label="16 Mar")
    ax.plot(centers, med17, "o-", color="#f58518", label="17 Mar")
    ax.fill_between(centers, p2516, p7516, color="#4c78a8", alpha=0.18, lw=0)
    ax.fill_between(centers, p2517, p7517, color="#f58518", alpha=0.18, lw=0)
    for x, y, d, a, b in zip(centers, med17, delta, n16, n17):
        if np.isfinite(y) and np.isfinite(d):
            ax.text(x, y + 0.045, f"{d:+.2f}", ha="center", va="bottom", fontsize=8)
            ax.text(x, 0.08, f"n={a}/{b}", ha="center", va="bottom", fontsize=7.5, color="0.35")
    ax.set_xlim(38.8, 66.2)
    ax.set_ylim(0, 1.1)
    ax.set_xlabel("Geographic latitude bin center (deg)")
    ax.set_ylabel("Median O/N2")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper right", frameon=True)
    ax.set_title(f"Latitudinal medians from the {UT_MIN:.0f}-{UT_MAX:.0f} UT subauroral swaths; labels show 17 Mar minus 16 Mar")

    fig.suptitle(f"{UT_MIN:.0f}-{UT_MAX:.0f} UT TIMED/GUVI O/N2 Observations in the Northern Subauroral Region", y=0.985, fontsize=13)
    fig.text(
        0.015,
        0.012,
        f"Only raw GUVI points from {UT_MIN:.0f}-{UT_MAX:.0f} UT and 40-65N are used. "
        "These observations sample the morning sector (~7-9 LT), not the modeled dusk SAPS sector.",
        fontsize=8.3,
        ha="left",
        va="bottom",
    )
    fig.tight_layout(rect=[0, 0.03, 1, 0.96])
    out = ROOT / "guvi_on2_7_11ut_subauroral_raw_comparison.png"
    fig.savefig(out)
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    main()

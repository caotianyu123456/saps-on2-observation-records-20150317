import csv
from pathlib import Path

import matplotlib.pyplot as plt
import netCDF4
import numpy as np


ROOT = Path(__file__).resolve().parent
GUVI_17 = ROOT / "timed_guvi_l3-on2_2015076_Av0100r000.nc"
DMSP_FILES = [
    ROOT / "dmsp_f17_ssies_20150317_parsed.csv",
    ROOT / "dmsp_f18_ssies_20150317_parsed.csv",
]


def read_guvi_raw(path):
    ds = netCDF4.Dataset(path)
    doy = np.asarray(ds.variables["FRACTIONAL_DOY"][:], dtype=float)
    on2 = np.asarray(ds.variables["ON2"][:], dtype=float)
    lat = np.asarray(ds.variables["LATITUDE"][:], dtype=float)
    lon = np.asarray(ds.variables["LONGITUDE"][:], dtype=float)
    sza = np.asarray(ds.variables["SOLAR ZENITH ANGLE"][:], dtype=float)
    ds.close()
    ut = (doy % 1.0) * 24.0
    lt = (ut + lon / 15.0) % 24.0
    valid = np.isfinite(on2) & (np.abs(on2) < 1e20) & np.isfinite(lat) & np.isfinite(lon)
    return {"ut": ut, "lt": lt, "lat": lat, "lon": lon, "on2": on2, "sza": sza, "valid": valid}


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
    return cols


def split_passes(indices, ut):
    if len(indices) == 0:
        return []
    groups = []
    start = 0
    for pos in range(1, len(indices)):
        if indices[pos] - indices[pos - 1] > 8 or ut[indices[pos]] - ut[indices[pos - 1]] > 0.18:
            groups.append(indices[start:pos])
            start = pos
    groups.append(indices[start:])
    return groups


def select_strong_passes(cols, mask, n_each=2):
    selected = []
    for sat in sorted(set(cols["satellite"])):
        sat_idx = np.where(mask & (cols["satellite"] == sat))[0]
        sat_idx = sat_idx[np.argsort(cols["ut"][sat_idx])]
        for group in split_passes(sat_idx, cols["ut"]):
            if len(group) < 160:
                continue
            drift = cols["horizontal_ion_drift_mps"][group]
            selected.append(
                {
                    "sat": sat,
                    "idx": group,
                    "t0": float(np.nanmin(cols["ut"][group])),
                    "t1": float(np.nanmax(cols["ut"][group])),
                    "absmax": float(np.nanmax(np.abs(drift))),
                    "median": float(np.nanmedian(drift)),
                }
            )
    out = []
    for sat in sorted(set(item["sat"] for item in selected)):
        items = [item for item in selected if item["sat"] == sat]
        out.extend(sorted(items, key=lambda item: item["absmax"], reverse=True)[:n_each])
    return sorted(out, key=lambda item: item["t0"])


def local_normals_display(ax, x, y):
    points = ax.transData.transform(np.column_stack([x, y]))
    tangent = np.gradient(points, axis=0)
    norm = np.hypot(tangent[:, 0], tangent[:, 1])
    ok = norm > 0
    tangent[ok] = tangent[ok] / norm[ok, None]
    normal = np.column_stack([-tangent[:, 1], tangent[:, 0]])
    flip = normal[:, 0] < 0
    normal[flip] *= -1
    return normal


def draw_speed_arrows(ax, cols, group, color="#7a1688"):
    idx = group["idx"]
    x = cols["glt"][idx]
    y = cols["glat"][idx]
    order = np.argsort(cols["ut"][idx])
    idx = idx[order]
    x = cols["glt"][idx]
    y = cols["glat"][idx]
    ax.plot(x, y, color=color, lw=1.9, alpha=0.85, zorder=5)
    normals = local_normals_display(ax, x, y)
    positions = np.arange(8, len(idx) - 8, 34)
    if len(positions) > 22:
        positions = positions[np.linspace(0, len(positions) - 1, 22, dtype=int)]
    for pos in positions:
        drift = cols["horizontal_ion_drift_mps"][idx[pos]]
        if not np.isfinite(drift):
            continue
        # Length in screen pixels. This keeps arrow shafts readable while
        # preserving speed scaling; values above 3 km/s are clipped visually.
        length_px = min(abs(drift), 3000.0) / 1000.0 * 16.0
        if length_px < 2.0:
            continue
        start = ax.transData.transform((x[pos], y[pos]))
        end = start + normals[pos] * length_px
        end_xy = ax.transData.inverted().transform(end)
        ax.annotate(
            "",
            xy=end_xy,
            xytext=(x[pos], y[pos]),
            arrowprops=dict(
                arrowstyle="-|>",
                color=color,
                lw=0.35,
                mutation_scale=3.0,
                shrinkA=0,
                shrinkB=0,
            ),
            zorder=7,
        )
    mid = idx[len(idx) // 2]
    ax.text(
        cols["glt"][mid] + 0.12,
        cols["glat"][mid],
        f"{group['sat']} {group['t0']:.2f}-{group['t1']:.2f} UT\nmax |Vi|={group['absmax']/1000:.1f} km/s",
        fontsize=7.4,
        color=color,
        ha="left",
        va="center",
        bbox=dict(fc="white", ec="none", alpha=0.74, pad=1.3),
        zorder=8,
    )


def main():
    guvi = read_guvi_raw(GUVI_17)
    cols = read_dmsp()

    guvi_mask = guvi["valid"] & (guvi["lat"] >= -80) & (guvi["lat"] <= -35)
    dmsp_mask = (
        (cols["glat"] >= -72)
        & (cols["glat"] <= -38)
        & (cols["glt"] >= 18)
        & (cols["glt"] <= 22.2)
    )
    target_mask = dmsp_mask & (cols["glat"] >= -70) & (cols["glat"] <= -40)
    strong = select_strong_passes(cols, target_mask, n_each=2)

    print("DMSP southern dusk/premidnight passes (40-70S, 18-24 LT):")
    for sat in sorted(set(cols["satellite"])):
        m = target_mask & (cols["satellite"] == sat)
        drift = cols["horizontal_ion_drift_mps"][m]
        print(
            "{}: n={}, GLT {:.2f}-{:.2f}, UT {:.2f}-{:.2f}, median |Vi| {:.0f} m/s, p95 |Vi| {:.0f} m/s, max |Vi| {:.0f} m/s".format(
                sat,
                int(m.sum()),
                np.nanmin(cols["glt"][m]),
                np.nanmax(cols["glt"][m]),
                np.nanmin(cols["ut"][m]),
                np.nanmax(cols["ut"][m]),
                np.nanmedian(np.abs(drift)),
                np.nanpercentile(np.abs(drift), 95),
                np.nanmax(np.abs(drift)),
            )
        )
    print("Selected strong passes:")
    for item in strong:
        print(f"  {item['sat']} UT {item['t0']:.2f}-{item['t1']:.2f}, max |Vi|={item['absmax']:.0f} m/s")

    lat_bins = np.arange(-70, -39.9, 5)
    centers = (lat_bins[:-1] + lat_bins[1:]) / 2
    med = np.full(len(centers), np.nan)
    p95 = np.full(len(centers), np.nan)
    mx = np.full(len(centers), np.nan)
    counts = np.zeros(len(centers), dtype=int)
    for i in range(len(centers)):
        m = target_mask & (cols["glat"] >= lat_bins[i]) & (cols["glat"] < lat_bins[i + 1])
        counts[i] = int(m.sum())
        if counts[i]:
            z = np.abs(cols["horizontal_ion_drift_mps"][m]) / 1000.0
            med[i] = np.nanmedian(z)
            p95[i] = np.nanpercentile(z, 95)
            mx[i] = np.nanmax(z)

    fig, axes = plt.subplots(2, 1, figsize=(11.2, 9.0), dpi=220, gridspec_kw={"height_ratios": [2.1, 1.0]})
    ax = axes[0]
    sc = ax.scatter(
        guvi["lt"][guvi_mask],
        guvi["lat"][guvi_mask],
        c=guvi["on2"][guvi_mask],
        s=10,
        cmap="viridis",
        vmin=0,
        vmax=1.1,
        linewidths=0,
        alpha=0.82,
        label="GUVI raw O/N2",
        zorder=2,
    )
    cbar = fig.colorbar(sc, ax=ax, pad=0.012)
    cbar.set_label("GUVI O/N2")

    drift_speed = np.abs(cols["horizontal_ion_drift_mps"][dmsp_mask]) / 1000.0
    dmsp_sc = ax.scatter(
        cols["glt"][dmsp_mask],
        cols["glat"][dmsp_mask],
        c=np.clip(drift_speed, 0, 4),
        s=8,
        cmap="magma",
        vmin=0,
        vmax=4,
        linewidths=0,
        alpha=0.50,
        zorder=4,
    )
    cbar2 = fig.colorbar(dmsp_sc, ax=ax, pad=0.080)
    cbar2.set_label("|DMSP Vi| (km/s), capped at 4")

    ax.plot([12, 18, 18, 12, 12], [-70, -70, -40, -40, -70], color="#ff7f0e", lw=2.0, ls="--")
    ax.text(12.15, -42, "GUVI valid\n12-18 LT\n40-70S", color="#9a4f00", fontsize=8.5, va="top")
    ax.plot([18, 22.2, 22.2, 18, 18], [-70, -70, -40, -40, -70], color="#7a1688", lw=2.0)
    ax.text(18.15, -42, "DMSP dusk\n18-22 LT\n40-70S", color="#7a1688", fontsize=8.5, va="top")

    fig.canvas.draw()
    for item in strong:
        draw_speed_arrows(ax, cols, item)

    ax.set_xlim(10, 22.5)
    ax.set_ylim(-80, -35)
    ax.set_xlabel("Observed local time (hour)")
    ax.set_ylabel("Geographic latitude (deg)")
    ax.set_title("17 Mar 2015: Southern Hemisphere GUVI O/N2 and DMSP horizontal ion drift")
    ax.grid(alpha=0.22)

    ax = axes[1]
    ax.plot(centers, med, "o-", color="0.35", label="median |Vi|")
    ax.plot(centers, p95, "s-", color="#d95f02", label="95th percentile |Vi|")
    ax.plot(centers, mx, "^-", color="#7a1688", label="max |Vi|")
    for x, y, n in zip(centers, p95, counts):
        if np.isfinite(y):
            ax.text(x, y + 0.12, f"n={n}", ha="center", va="bottom", fontsize=7.5, color="0.35")
    ax.set_xlim(-71, -39)
    ax.set_ylim(0, 5.4)
    ax.set_xlabel("Geographic latitude bin center (deg)")
    ax.set_ylabel("|Vi| (km/s)")
    ax.set_title("DMSP drift statistics in 40-70S, 18-24 LT")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper right", frameon=True)

    fig.suptitle("Southern Subauroral O/N2 Coverage and DMSP Drift Peaks", y=0.985, fontsize=14)
    fig.text(
        0.015,
        0.012,
        "GUVI points use the retrieval local time. DMSP tracks use spacecraft geographic local time. "
        "The strongest DMSP drift peaks are in the southern dusk/premidnight sector, while valid GUVI O/N2 points are earlier in local time.",
        ha="left",
        va="bottom",
        fontsize=8.2,
    )
    fig.tight_layout(rect=[0, 0.035, 1, 0.96])
    out = ROOT / "guvi_dmsp_southern_subauroral_overlay.png"
    fig.savefig(out)
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    main()

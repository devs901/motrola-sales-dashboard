"""Render docs/dashboard-preview.png from the CSVs (a preview of the report you build in Power BI)."""
from pathlib import Path
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch

H = Path(__file__).parent; D = H / "data"
s = pd.read_csv(D / "fact_sales.csv", parse_dates=["order_date"])
p, rg, ch = (pd.read_csv(D / f"dim_{x}.csv") for x in ("product", "region", "channel"))
s["rev"] = s.units * s.unit_price; s["cost"] = s.units * s.unit_cost; s["mrpv"] = s.units * s.mrp
s = s.merge(p[["product_id", "model", "series"]], on="product_id").merge(rg, on="region_id").merge(ch, on="channel_id")

# dark theme (colors validated with the dataviz palette validator, dark mode)
BG, CARD, INK, SUB, GRID = "#0e1014", "#1a1a19", "#f0efec", "#a3a29a", "#2c2c2a"
BLUE, ORANGE, AQUA = "#3987e5", "#d95926", "#199e70"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK})
fig = plt.figure(figsize=(16, 9.6), dpi=110, facecolor=BG)

rev, units = s.rev.sum() / 1e7, s.units.sum()
gm = 1 - s.cost.sum() / s.rev.sum(); disc = 1 - s.rev.sum() / s.mrpv.sum(); ret = s.returned.mean()
ytd = lambda y: s[(s.order_date.dt.year == y) & (s.order_date.dt.month <= 10)].rev.sum()
yoy = ytd(2026) / ytd(2025) - 1

# header
fig.text(0.03, 0.953, "MOTOROLA  MOBILE SALES", fontsize=23, fontweight="bold", va="center")
fig.text(0.03, 0.912, "India  ·  Jan 2025 – Oct 2026  ·  simulated practice data, not real company sales", fontsize=10.5, color=SUB, va="center")
for i, t in enumerate(["Overview", "Products", "Regions", "Channels"]):
    x = 0.69 + i * 0.075
    fig.patches.append(FancyBboxPatch((x, 0.935), 0.068, 0.032, boxstyle="round,pad=0,rounding_size=0.012", transform=fig.transFigure,
                       fc=BLUE if i == 0 else CARD, ec="none", zorder=0))
    fig.text(x + 0.034, 0.951, t, ha="center", va="center", fontsize=10, fontweight="bold" if i == 0 else "normal", color="white" if i == 0 else SUB)

def card(rect, radius=0.012):
    fig.patches.append(FancyBboxPatch((rect[0], rect[1]), rect[2], rect[3], boxstyle=f"round,pad=0,rounding_size={radius}",
                       transform=fig.transFigure, fc=CARD, ec=GRID, lw=.8, zorder=0))

# KPI cards with accent strip
kpis = [("REVENUE", f"₹{rev:,.1f} Cr", None, BLUE), ("UNITS SOLD", f"{units:,}", None, BLUE), ("GROSS MARGIN", f"{gm*100:.1f}%", None, AQUA),
        ("AVG DISCOUNT", f"{disc*100:.1f}%", None, ORANGE), ("RETURN RATE", f"{ret*100:.1f}%", None, ORANGE), ("YoY GROWTH (JAN–OCT)", f"▲ {yoy*100:.1f}%", None, AQUA)]
for i, (k, v, _, c) in enumerate(kpis):
    x = 0.03 + i * 0.1615
    card([x, 0.795, 0.150, 0.092])
    fig.patches.append(FancyBboxPatch((x + 0.012, 0.795 + 0.092 - 0.0125), 0.026, 0.0045, boxstyle="round,pad=0,rounding_size=0.002", transform=fig.transFigure, fc=c, ec="none", zorder=1))
    fig.text(x + 0.012, 0.848, k, fontsize=8.5, color=SUB, fontweight="bold")
    fig.text(x + 0.012, 0.812, v, fontsize=20, fontweight="bold")

def panel(rect, title, sub, cx):
    card([cx[0], rect[1] - 0.052, cx[1] - cx[0], rect[3] + 0.112])
    ax = fig.add_axes(rect); ax.set_facecolor("none"); ax.set_zorder(5)
    for k in ("top", "right", "left"): ax.spines[k].set_visible(False)
    ax.spines["bottom"].set_color(GRID); ax.tick_params(colors=SUB, labelsize=9, length=0)
    ax.grid(axis="y", color=GRID, lw=.7); ax.set_axisbelow(True)
    fig.text(cx[0] + 0.014, rect[1] + rect[3] + 0.030, title, fontsize=11.5, fontweight="bold", va="center")
    fig.text(cx[0] + 0.014, rect[1] + rect[3] + 0.008, sub, fontsize=8.5, color=SUB, va="center")
    return ax

# 1) monthly revenue, 2025 vs 2026 (area + line)
m = s.assign(y=s.order_date.dt.year, mo=s.order_date.dt.month).groupby(["y", "mo"]).rev.sum().unstack(0).div(1e7)
ax = panel([0.065, 0.455, 0.405, 0.235], "Monthly revenue", "₹ crore · 2026 vs 2025", (0.03, 0.485))
ax.plot(m.index, m[2025], color=ORANGE, lw=2.2, marker="o", ms=5, mfc=CARD, mew=2)
x6, y6 = m[2026].dropna().index, m[2026].dropna()
ax.fill_between(x6, y6, color=BLUE, alpha=.16); ax.plot(x6, y6, color=BLUE, lw=2.6, marker="o", ms=5.5, mfc=CARD, mew=2)
ax.set_xticks(range(1, 13)); ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]); ax.set_ylim(0, 9.8)
ax.text(8.85, 7.3, f"Oct 2025  ₹{m.loc[10, 2025]:.1f} Cr", ha="right", fontsize=9, color="#ee8a60", fontweight="bold")
ax.text(8.85, 8.7, f"Oct 2026  ₹{m.loc[10, 2026]:.1f} Cr", ha="right", fontsize=9, color="#6fa8f0", fontweight="bold")
ax.text(1.0, 9.0, "● 2026", color=BLUE, fontsize=9.5, fontweight="bold"); ax.text(2.3, 9.0, "● 2025", color=ORANGE, fontsize=9.5, fontweight="bold")

# 2) revenue by model
t = s.groupby("model").rev.sum().sort_values().div(1e7)
ax = panel([0.615, 0.455, 0.335, 0.235], "Revenue by model", "₹ crore · top seller highlighted", (0.515, 0.97))
ax.grid(axis="y", visible=False); ax.grid(axis="x", color=GRID, lw=.7); ax.spines["bottom"].set_visible(False); ax.set_xticks([])
cols = [BLUE if v == t.max() else "#2b5f9e" for v in t.values]
b = ax.barh(t.index, t.values, color=cols, height=.62)
for r, v in zip(b, t.values): ax.text(v + .2, r.get_y() + r.get_height() / 2, f"{v:.1f}", va="center", fontsize=9, fontweight="bold")
ax.set_xlim(0, t.max() * 1.15); ax.tick_params(axis="y", labelsize=8.5, colors=INK)

# 3) channel share
t = s.groupby("channel").rev.sum().sort_values(ascending=False).div(s.rev.sum()) * 100
ax = panel([0.05, 0.085, 0.255, 0.235], "Channel mix", "% of revenue", (0.03, 0.315))
b = ax.bar(t.index, t.values, color=BLUE, width=.56); ax.set_ylim(0, 46); ax.set_yticks([])
ax.grid(axis="y", visible=False)
for r, v in zip(b, t.values): ax.text(r.get_x() + r.get_width() / 2, v + 1.2, f"{v:.0f}%", ha="center", fontsize=10.5, fontweight="bold")
ax.tick_params(axis="x", labelsize=8.5)

# 4) heatmap zone x quarter
q = s.assign(q=s.order_date.dt.to_period("Q").astype(str)).pivot_table(index="zone", columns="q", values="rev", aggfunc="sum").div(1e7)
q = q.loc[q.sum(axis=1).sort_values(ascending=False).index]
ax = panel([0.405, 0.085, 0.245, 0.235], "Revenue by zone and quarter", "₹ crore · lighter = higher · Q4 2026 = Oct only", (0.335, 0.665))
ax.grid(False); ax.spines["bottom"].set_visible(False)
cm = LinearSegmentedColormap.from_list("blu", ["#1c2f4a", "#2b5f9e", "#6fa8f0"])
ax.imshow(q.values, cmap=cm, aspect="auto")
for (i, j), v in np.ndenumerate(q.values):
    ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=8.5, color="white", fontweight="bold")
ax.set_xticks(range(q.shape[1])); ax.set_xticklabels([c.replace("2025", "'25").replace("2026", "'26") for c in q.columns], fontsize=8)
ax.set_yticks(range(q.shape[0])); ax.set_yticklabels(q.index, fontsize=9, color=INK)
for k in range(q.shape[0] + 1): ax.axhline(k - .5, color=CARD, lw=2)
for k in range(q.shape[1] + 1): ax.axvline(k - .5, color=CARD, lw=2)

# 5) margin by series
t = s.groupby("series").agg(rev=("rev", "sum"), cost=("cost", "sum")); t["gm"] = (1 - t.cost / t.rev) * 100; t = t.sort_values("gm")
ax = panel([0.785, 0.085, 0.165, 0.235], "Gross margin by series", "% of revenue", (0.685, 0.97))
ax.grid(axis="y", visible=False); ax.spines["bottom"].set_visible(False); ax.set_xticks([])
b = ax.barh(t.index, t.gm, color=AQUA, height=.55)
for r, v in zip(b, t.gm): ax.text(v + .3, r.get_y() + r.get_height() / 2, f"{v:.1f}%", va="center", fontsize=10, fontweight="bold")
ax.set_xlim(0, t.gm.max() * 1.25); ax.tick_params(axis="y", labelsize=9, colors=INK)

fig.text(0.03, 0.010, "Preview rendered with Python from the same CSVs. Build the interactive version in Power BI Desktop using the README steps.", fontsize=9, color=SUB)
(H / "docs").mkdir(exist_ok=True)
fig.savefig(H / "docs" / "dashboard-preview.png", facecolor=BG)
print("saved")

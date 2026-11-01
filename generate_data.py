"""Generate SIMULATED Motorola-style mobile sales data for a Power BI dashboard.

IMPORTANT: this is practice data. It is randomly generated (seeded, repeatable).
It is NOT Motorola's real sales, and prices/launch dates are illustrative only.

Run:  python generate_data.py   -> writes CSV files into ./data
"""
from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
OUT = Path(__file__).parent / "data"; OUT.mkdir(exist_ok=True)
START, END = pd.Timestamp("2025-01-01"), pd.Timestamp("2026-10-31")

# ---------------- dim_product (illustrative models & prices, INR) ----------------
P = [  # model, series, ram, storage, launch, mrp, cost_ratio, base popularity
    ("moto e14",            "E Series",    4,  64, "2025-02-01",  7499, 0.80, 9),
    ("moto g45 5G",         "G Series",    8, 128, "2024-08-01", 12999, 0.80, 14),
    ("moto g64 5G",         "G Series",    8, 128, "2024-04-01", 15999, 0.79, 12),
    ("moto g85 5G",         "G Series",    8, 128, "2024-07-01", 19999, 0.78, 13),
    ("moto g85 5G Pro",     "G Series",   12, 256, "2025-03-01", 22999, 0.78, 7),
    ("edge 50 Fusion",      "Edge Series", 8, 128, "2024-05-01", 24999, 0.76, 9),
    ("edge 50 Neo",         "Edge Series", 8, 256, "2024-10-01", 27999, 0.76, 7),
    ("edge 60 Fusion",      "Edge Series", 8, 256, "2025-04-01", 25999, 0.76, 10),
    ("edge 60 Pro",         "Edge Series",12, 256, "2025-05-01", 33999, 0.75, 5),
    ("razr 60",             "Razr Foldable", 8, 256, "2025-06-01", 54999, 0.72, 2.2),
]
dim_product = pd.DataFrame(P, columns=["model", "series", "ram_gb", "storage_gb", "launch_date", "mrp", "cost_ratio", "popularity"])
dim_product.insert(0, "product_id", range(1, len(P) + 1))
dim_product["variant"] = dim_product.ram_gb.astype(str) + "GB/" + dim_product.storage_gb.astype(str) + "GB"
dim_product["unit_cost"] = (dim_product.mrp * dim_product.cost_ratio).round()
dim_product["price_band"] = pd.cut(dim_product.mrp, [0, 10000, 20000, 30000, 1e9], labels=["Entry (<10k)", "Budget (10-20k)", "Mid (20-30k)", "Premium (30k+)"]).astype(str)
dim_product[["product_id", "model", "variant", "series", "price_band", "launch_date", "mrp", "unit_cost"]].to_csv(OUT / "dim_product.csv", index=False)

# ---------------- dim_region ----------------
R = [("Maharashtra", "West", "Mumbai", 13), ("Gujarat", "West", "Ahmedabad", 7), ("Karnataka", "South", "Bengaluru", 9),
     ("Tamil Nadu", "South", "Chennai", 8), ("Telangana", "South", "Hyderabad", 6), ("Kerala", "South", "Kochi", 4),
     ("Uttar Pradesh", "North", "Lucknow", 14), ("Delhi NCR", "North", "New Delhi", 9), ("Rajasthan", "North", "Jaipur", 5),
     ("West Bengal", "East", "Kolkata", 7), ("Bihar", "East", "Patna", 6), ("Madhya Pradesh", "Central", "Bhopal", 6)]
dim_region = pd.DataFrame(R, columns=["state", "zone", "hub_city", "weight"])
dim_region.insert(0, "region_id", range(1, len(R) + 1))
dim_region[["region_id", "state", "zone", "hub_city"]].to_csv(OUT / "dim_region.csv", index=False)

# ---------------- dim_channel ----------------
C = [("Flipkart", "Online marketplace"), ("Amazon", "Online marketplace"), ("Motorola.in", "Brand website"), ("Offline retail", "Retail stores")]
dim_channel = pd.DataFrame(C, columns=["channel", "channel_type"]); dim_channel.insert(0, "channel_id", range(1, 5))
dim_channel.to_csv(OUT / "dim_channel.csv", index=False)

# ---------------- dim_date ----------------
d = pd.date_range(START, END, freq="D")
dim_date = pd.DataFrame({"date": d, "year": d.year, "month_num": d.month, "month_name": d.strftime("%b"),
                         "month_start": d.to_period("M").to_timestamp(), "year_month": d.strftime("%Y-%m"),
                         "quarter": "Q" + d.quarter.astype(str), "weekday": d.strftime("%a"), "weekday_num": d.weekday + 1})
dim_date.to_csv(OUT / "dim_date.csv", index=False)

# ---------------- fact_sales (order lines) ----------------
N = 48000
season = {1: 1.15, 2: .85, 3: .9, 4: .9, 5: .95, 6: .85, 7: .9, 8: 1.15, 9: 1.1, 10: 1.7, 11: 1.3, 12: 1.0}  # Jan/Aug sales, festive Oct
dw = np.array([season[x.month] * (1 + 0.45 * (x - START).days / 668) * (1.2 if x.weekday() >= 5 else 1.0) for x in d])
dates = d[rng.choice(len(d), N, p=dw / dw.sum())]

# product choice depends on how old the product is on that date (launch spike, slow decay)
launch = pd.to_datetime(dim_product.launch_date).to_numpy()
age = (dates.to_numpy()[:, None] - launch[None, :]).astype("timedelta64[D]").astype(float)
fresh = np.where(age < 0, 0.0, 1.0 + 1.3 * np.exp(-np.clip(age, 0, None) / 90.0) - 0.0006 * np.clip(age, 0, 700))
W = fresh * dim_product.popularity.to_numpy()[None, :]
W = W / W.sum(axis=1, keepdims=True)
product_id = (rng.random(N)[:, None] > W.cumsum(axis=1)).sum(axis=1) + 1

region_id = rng.choice(dim_region.region_id, N, p=dim_region.weight / dim_region.weight.sum())
mrp = dim_product.set_index("product_id").mrp
cost = dim_product.set_index("product_id").unit_cost
price_tier = np.array([mrp[p] for p in product_id])

# channel mix varies with price (premium sells more offline / brand site)
cp = np.array([[.47, .27, .05, .21], [.44, .24, .06, .26], [.36, .20, .08, .36], [.28, .16, .10, .46]])
tier = np.digitize(price_tier, [10000, 20000, 30000])
channel_id = np.array([rng.choice(4, p=cp[t]) for t in tier]) + 1

# discount: deeper on marketplaces and during sale months, older models get discounted more
sale_boost = np.array([{1: 4, 8: 4, 10: 7, 11: 5}.get(m, 0) for m in dates.month])
ch_base = np.array([0, 9, 8, 3, 2])[channel_id]  # index 1..4
age_p = np.array([age[i, product_id[i] - 1] for i in range(N)])
disc = np.clip(ch_base + sale_boost + np.clip(age_p, 0, 600) / 100 + rng.normal(0, 1.5, N), 0, 30).round(1)
unit_price = (price_tier * (1 - disc / 100)).round()
units = rng.choice([1, 2, 3], N, p=[.9, .08, .02])
returned = (rng.random(N) < (0.035 + 0.02 * (channel_id <= 2) + 0.03 * (price_tier > 50000) - 0.01 * (channel_id == 4))).astype(int)
rating = np.where(rng.random(N) < 0.55, np.clip(rng.normal(4.1 - 0.9 * returned, 0.7, N), 1, 5).round(), np.nan)

fact_sales = pd.DataFrame({
    "order_line_id": np.arange(1, N + 1), "order_date": dates, "product_id": product_id, "region_id": region_id,
    "channel_id": channel_id, "units": units, "mrp": price_tier, "discount_pct": disc, "unit_price": unit_price,
    "unit_cost": [cost[p] for p in product_id], "returned": returned, "customer_rating": rating,
}).sort_values("order_date")
fact_sales["order_line_id"] = np.arange(1, N + 1)
fact_sales.to_csv(OUT / "fact_sales.csv", index=False)

for f in sorted(OUT.glob("*.csv")):
    print(f"{f.name:20s} {len(pd.read_csv(f)):>7,d} rows")

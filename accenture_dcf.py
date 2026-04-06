
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import warnings
warnings.filterwarnings('ignore')

TICKER = "ACN"

def safe_val(df, label, col_idx=0):
    try:
        if label in df.index:
            v = df.loc[label].iloc[col_idx]
            return float(v) if pd.notna(v) else np.nan
        return np.nan
    except Exception:
        return np.nan

def fetch_data():
    t    = yf.Ticker(TICKER)
    info = t.info
    inc  = t.income_stmt
    cf   = t.cashflow
    bal  = t.balance_sheet
    return t, info, inc, cf, bal

def compute_historical_fcff(inc, cf, tax_rate=0.22):
    records = []
    for yr in inc.columns:
        try:
            col_i = inc.columns.get_loc(yr)
            cf_i  = cf.columns.get_loc(yr)

            ebit  = safe_val(inc, "EBIT",                          col_i)
            da    = safe_val(cf,  "Depreciation And Amortization", cf_i)
            capex = abs(safe_val(cf, "Capital Expenditure",        cf_i))
            dwc   = safe_val(cf,  "Change In Working Capital",     cf_i)
            rev   = safe_val(inc, "Total Revenue",                 col_i)

            if any(np.isnan(v) for v in [ebit, da, capex]):
                continue

            dwc  = 0 if np.isnan(dwc) else dwc
            fcff = ebit * (1 - tax_rate) + da - capex - dwc

            records.append({
                "Fiscal Year":   str(yr.year),
                "Revenue ($B)":  round(rev / 1e9, 2) if not np.isnan(rev) else np.nan,
                "EBIT ($B)":     round(ebit / 1e9, 2),
                "D&A ($B)":      round(da / 1e9, 2),
                "CapEx ($B)":    round(capex / 1e9, 2),
                "ΔWC ($B)":      round(dwc / 1e9, 2),
                "FCFF ($B)":     round(fcff / 1e9, 2),
                "EBIT Margin %": round(ebit / rev * 100, 1) if not np.isnan(rev) and rev > 0 else np.nan,
                "fcff_raw":      fcff,
            })
        except Exception:
            continue
    return pd.DataFrame(records)

def compute_wacc(info, bal, tax_rate=0.22):
    RF   = 0.042
    ERP  = 0.055
    beta = info.get("beta", 1.1) or 1.1
    ke   = RF + beta * ERP

    try:
        debt_val = safe_val(bal, "Total Debt")
        int_exp  = abs(float(info.get("interestExpense", 0) or 0))
        kd = int_exp / debt_val if (debt_val and debt_val > 0 and not np.isnan(debt_val)) else 0.04
    except Exception:
        kd = 0.04

    mkt_cap    = info.get("marketCap", 0) or 0
    total_debt = safe_val(bal, "Total Debt")
    total_debt = 0 if np.isnan(total_debt) else total_debt
    V  = mkt_cap + total_debt
    we = mkt_cap / V if V > 0 else 0.94
    wd = total_debt / V if V > 0 else 0.06

    wacc = ke * we + kd * (1 - tax_rate) * wd
    return {
        "beta": round(beta, 2), "rf": RF, "erp": ERP,
        "ke": round(ke, 4), "kd": round(kd, 4),
        "tax_rate": tax_rate, "we": round(we, 4),
        "wd": round(wd, 4), "wacc": round(wacc, 4),
        "mkt_cap_B": round(mkt_cap / 1e9, 1),
        "total_debt_B": round(total_debt / 1e9, 1),
    }

def run_dcf(fcff_base, net_debt, shares, curr_px,
            fcff_growth, terminal_growth, wacc,
            forecast_years=5, label=""):
    fcffs    = [fcff_base * (1 + fcff_growth)**i for i in range(1, forecast_years + 1)]
    pv_fcffs = [f / (1 + wacc)**i for i, f in enumerate(fcffs, 1)]

    tv    = fcffs[-1] * (1 + terminal_growth) / (wacc - terminal_growth)
    pv_tv = tv / (1 + wacc)**forecast_years

    ev           = sum(pv_fcffs) + pv_tv
    equity_value = ev - net_debt
    price_target = equity_value / shares
    upside       = (price_target - curr_px) / curr_px * 100 if curr_px > 0 else 0
    tv_pct       = pv_tv / ev * 100 if ev > 0 else 0

    return {
        "label":           label,
        "fcff_growth":     fcff_growth,
        "terminal_growth": terminal_growth,
        "wacc":            wacc,
        "pv_fcffs_B":      [round(v / 1e9, 2) for v in pv_fcffs],
        "pv_tv_B":         round(pv_tv / 1e9, 2),
        "ev_B":            round(ev / 1e9, 1),
        "equity_val_B":    round(equity_value / 1e9, 1),
        "price_target":    round(price_target, 2),
        "current_price":   round(curr_px, 2),
        "upside_pct":      round(upside, 1),
        "tv_pct_of_ev":    round(tv_pct, 1),
        "fcff_proj_B":     [round(f / 1e9, 2) for f in fcffs],
    }

def sensitivity_table(fcff_base, net_debt, shares,
                       wacc_range, tg_range, base_growth=0.08, forecast_years=5):
    table = {}
    for tg in tg_range:
        row = {}
        for wacc in wacc_range:
            col = f"WACC {wacc:.1%}"
            if wacc <= tg:
                row[col] = np.nan
                continue
            fcffs    = [fcff_base * (1 + base_growth)**i for i in range(1, forecast_years + 1)]
            pv_fcffs = [f / (1 + wacc)**i for i, f in enumerate(fcffs, 1)]
            tv       = fcffs[-1] * (1 + tg) / (wacc - tg)
            pv_tv    = tv / (1 + wacc)**forecast_years
            price    = (sum(pv_fcffs) + pv_tv - net_debt) / shares
            row[col] = round(price, 1)
        table[f"TG {tg:.1%}"] = row
    return pd.DataFrame(table).T

# ── STREAMLIT APP ─────────────────────────────────────────────────────────────

st.set_page_config(page_title="Accenture DCF", page_icon="📊", layout="wide")
st.title("Accenture (ACN) — DCF / FCFF Valuation")
st.caption("NYSE: ACN · IT Services & Consulting · FY ends August 31")

# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Model Assumptions")

    st.subheader("WACC Inputs")
    rf      = st.slider("Risk-Free Rate (%)",  2.0, 6.0, 4.2, 0.1) / 100
    erp     = st.slider("Equity Risk Premium (%)", 3.0, 8.0, 5.5, 0.1) / 100
    beta_ov = st.slider("Beta Override", 0.5, 2.0, 1.1, 0.05)

    st.subheader("Scenario Parameters")
    st.markdown("**Bull Case**")
    bull_g  = st.slider("Bull FCFF Growth (%)",  5, 20, 12, 1) / 100
    bull_tg = st.slider("Bull Terminal Growth (%)", 2.0, 6.0, 4.0, 0.5) / 100
    bull_w  = st.slider("Bull WACC (%)", 7.0, 12.0, 9.0, 0.5) / 100

    st.markdown("**Base Case**")
    base_g  = st.slider("Base FCFF Growth (%)", 3, 15, 8, 1) / 100
    base_tg = st.slider("Base Terminal Growth (%)", 1.5, 5.0, 3.5, 0.5) / 100
    base_w  = st.slider("Base WACC (%)", 8.0, 13.0, 10.0, 0.5) / 100

    st.markdown("**Bear Case**")
    bear_g  = st.slider("Bear FCFF Growth (%)", 0, 8, 3, 1) / 100
    bear_tg = st.slider("Bear Terminal Growth (%)", 1.0, 4.0, 2.5, 0.5) / 100
    bear_w  = st.slider("Bear WACC (%)", 9.0, 14.0, 11.5, 0.5) / 100

    st.subheader("Sensitivity Range")
    wacc_min = st.slider("WACC Min (%)", 7.0, 10.0, 8.5, 0.5) / 100
    wacc_max = st.slider("WACC Max (%)", 10.0, 14.0, 11.5, 0.5) / 100
    tg_min   = st.slider("Terminal Growth Min (%)", 1.0, 3.0, 2.0, 0.5) / 100
    tg_max   = st.slider("Terminal Growth Max (%)", 3.0, 6.0, 4.5, 0.5) / 100

# ── Fetch data ────────────────────────────────────────────────────────────────
with st.spinner("Fetching Accenture data from Yahoo Finance..."):
    t, info, inc, cf, bal = fetch_data()

curr_px = info.get("currentPrice", 0) or 0
mktcap  = info.get("marketCap",    0) or 0
shares  = info.get("sharesOutstanding", 622e6) or 622e6

# ── Snapshot metrics ──────────────────────────────────────────────────────────
st.subheader("Company Snapshot")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Price",       f"${curr_px:.2f}")
c2.metric("Market Cap",  f"${mktcap/1e9:.0f}B")
c3.metric("Trailing P/E", f"{info.get('trailingPE', 0) or 0:.1f}x")
c4.metric("Forward P/E", f"{info.get('forwardPE', 0) or 0:.1f}x")
c5.metric("EV/EBITDA",   f"{info.get('enterpriseToEbitda', 0) or 0:.1f}x")
c6.metric("Sector",      "IT Services")

st.divider()

# ── Historical FCFF ───────────────────────────────────────────────────────────
st.subheader("Historical FCFF")
hist_df = compute_historical_fcff(inc, cf)

if not hist_df.empty:
    FCFF_BASE = hist_df["fcff_raw"].iloc[0]

    col_l, col_r = st.columns([2, 1])
    with col_l:
        fig_h = go.Figure()
        fig_h.add_bar(
            x=hist_df["Fiscal Year"], y=hist_df["FCFF ($B)"],
            marker_color="#3b82f6", name="FCFF",
            text=[f"${v}B" for v in hist_df["FCFF ($B)"]],
            textposition="outside"
        )
        fig_h.add_trace(go.Scatter(
            x=hist_df["Fiscal Year"], y=hist_df["Revenue ($B)"],
            mode="lines+markers", name="Revenue",
            line=dict(color="#f59e0b", width=2), yaxis="y2"
        ))
        fig_h.update_layout(
            template="plotly_dark", height=350,
            title="FCFF vs Revenue ($B)",
            yaxis=dict(title="FCFF ($B)"),
            yaxis2=dict(title="Revenue ($B)", overlaying="y", side="right"),
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig_h, use_container_width=True)

    with col_r:
        st.dataframe(
            hist_df.drop(columns=["fcff_raw"]).set_index("Fiscal Year"),
            use_container_width=True
        )
        vals = hist_df["FCFF ($B)"].dropna().tolist()
        if len(vals) >= 2 and vals[-1] > 0:
            n    = len(vals) - 1
            cagr = (vals[0] / vals[-1])**(1/n) - 1
            st.metric("FCFF CAGR", f"{cagr*100:.1f}%")
else:
    FCFF_BASE = 8.6e9
    st.warning("Using fallback FCFF: $8.6B (FY2024 actual)")

st.divider()

# ── WACC ──────────────────────────────────────────────────────────────────────
st.subheader("WACC Breakdown")
wacc_data = compute_wacc(info, bal)

# Override with sidebar values
ke_ov   = rf + beta_ov * erp
wacc_ov = ke_ov * wacc_data["we"] + wacc_data["kd"] * (1 - wacc_data["tax_rate"]) * wacc_data["wd"]

w1, w2, w3, w4, w5, w6 = st.columns(6)
w1.metric("Beta",            f"{beta_ov:.2f}")
w2.metric("Risk-Free Rate",  f"{rf*100:.1f}%")
w3.metric("Cost of Equity",  f"{ke_ov*100:.2f}%")
w4.metric("Cost of Debt",    f"{wacc_data['kd']*100:.2f}%")
w5.metric("WACC",            f"{wacc_ov*100:.2f}%")
w6.metric("Equity Weight",   f"{wacc_data['we']*100:.0f}%")

st.divider()

# ── Net debt ──────────────────────────────────────────────────────────────────
try:
    cash_val = safe_val(bal, "Cash And Cash Equivalents")
    debt_val = safe_val(bal, "Total Debt")
    cash_val = 0 if np.isnan(cash_val) else cash_val
    debt_val = 0 if np.isnan(debt_val) else debt_val
    NET_DEBT = debt_val - cash_val
except Exception:
    NET_DEBT = 0

# ── Run scenarios ─────────────────────────────────────────────────────────────
st.subheader("Scenario Analysis")

scenario_params = {
    "Bull": (bull_g,  bull_tg,  bull_w,  "#22c55e"),
    "Base": (base_g,  base_tg,  base_w,  "#3b82f6"),
    "Bear": (bear_g,  bear_tg,  bear_w,  "#ef4444"),
}

results = {}
for name, (g, tg, w, _) in scenario_params.items():
    try:
        results[name] = run_dcf(
            FCFF_BASE, NET_DEBT, shares, curr_px,
            fcff_growth=g, terminal_growth=tg, wacc=w, label=name
        )
    except ValueError as e:
        st.error(f"{name} scenario error: {e}")

if results:
    # Metrics
    mc = st.columns(len(results))
    for col, (name, r) in zip(mc, results.items()):
        col.metric(
            name,
            f"${r['price_target']}",
            f"{r['upside_pct']:+.1f}%"
        )

    # Bar chart
    names   = list(results.keys())
    targets = [results[n]["price_target"] for n in names]
    colors  = [scenario_params[n][3] for n in names]

    fig_s = go.Figure()
    for name, target, color in zip(names, targets, colors):
        fig_s.add_bar(
            x=[name], y=[target],
            marker_color=color,
            text=[f"${target}"],
            textposition="outside",
            width=0.4
        )
    fig_s.add_hline(
        y=curr_px, line_dash="dash", line_color="white",
        annotation_text=f"Current ${curr_px:.2f}",
        annotation_font_color="white"
    )
    fig_s.update_layout(
        template="plotly_dark", height=420,
        title="Price Target by Scenario",
        yaxis_title="Price per Share ($)",
        showlegend=False,
        yaxis=dict(range=[0, max(targets) * 1.2])
    )
    st.plotly_chart(fig_s, use_container_width=True)

    # Summary table
    rows = []
    for name, r in results.items():
        rows.append({
            "Scenario":        name,
            "FCFF Growth":     f"{r['fcff_growth']:.0%}",
            "Terminal Growth": f"{r['terminal_growth']:.1%}",
            "WACC":            f"{r['wacc']:.1%}",
            "EV ($B)":         f"${r['ev_B']}B",
            "Price Target":    f"${r['price_target']}",
            "Upside":          f"{r['upside_pct']:+.1f}%",
            "TV % of EV":      f"{r['tv_pct_of_ev']}%",
        })
    st.dataframe(pd.DataFrame(rows).set_index("Scenario"), use_container_width=True)

st.divider()

# ── Base case FCFF projection ─────────────────────────────────────────────────
if "Base" in results:
    st.subheader("Base Case — Projected FCFF ($B)")
    base = results["Base"]
    yrs  = [f"FY{2025+i}" for i in range(5)]

    fig_p = go.Figure()
    fig_p.add_bar(
        x=yrs, y=base["fcff_proj_B"],
        marker_color="#3b82f6",
        text=[f"${v}B" for v in base["fcff_proj_B"]],
        textposition="outside"
    )
    fig_p.update_layout(
        template="plotly_dark", height=340,
        yaxis_title="FCFF ($B)"
    )
    st.plotly_chart(fig_p, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("PV of FCFFs",   f"${sum(base['pv_fcffs_B']):.1f}B")
    c2.metric("PV of TV",      f"${base['pv_tv_B']:.1f}B")
    c3.metric("TV % of EV",    f"{base['tv_pct_of_ev']}%",
              delta="⚠ High" if base["tv_pct_of_ev"] > 70 else "OK",
              delta_color="inverse" if base["tv_pct_of_ev"] > 70 else "normal")

st.divider()

# ── Sensitivity table ─────────────────────────────────────────────────────────
st.subheader("Sensitivity — Price per Share ($)")
st.caption("Rows = Terminal Growth | Columns = WACC | Base FCFF growth = 8%")

wacc_range = list(np.arange(wacc_min, wacc_max + 0.005, 0.005))
tg_range   = list(np.arange(tg_min,   tg_max   + 0.005, 0.005))

sens_df = sensitivity_table(FCFF_BASE, NET_DEBT, shares, wacc_range, tg_range)

def colour_cell(val):
    if pd.isna(val):
        return "color: gray"
    if val > curr_px * 1.15:
        return "background-color: #14532d; color: white"
    elif val > curr_px:
        return "background-color: #166534; color: white"
    elif val > curr_px * 0.85:
        return "background-color: #7f1d1d; color: white"
    else:
        return "background-color: #450a0a; color: white"

st.dataframe(
    sens_df.style.applymap(colour_cell).format("${:.1f}", na_rep="N/M"),
    use_container_width=True
)
st.caption(
    f"Dark green = >15% upside | Light green = upside | "
    f"Red = downside | Current price: ${curr_px:.2f}"
)

st.divider()

# ── Export ────────────────────────────────────────────────────────────────────
st.subheader("Export")
if not hist_df.empty and results:
    import io
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        hist_df.drop(columns=["fcff_raw"]).to_excel(
            writer, sheet_name="Historical FCFF", index=False
        )
        pd.DataFrame(rows).to_excel(
            writer, sheet_name="Scenarios", index=False
        )
        sens_df.to_excel(writer, sheet_name="Sensitivity")

    st.download_button(
        label="Download Excel Model",
        data=buf.getvalue(),
        file_name="Accenture_DCF.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

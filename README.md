# 📊 Accenture (ACN) — DCF / FCFF Valuation Model

A fully interactive **Discounted Cash Flow (DCF)** valuation dashboard for **Accenture PLC (NYSE: ACN)**, built with Python and Streamlit. Fetches live financial data from Yahoo Finance, computes FCFF-based intrinsic value, and presents Bull / Base / Bear scenarios with an interactive sensitivity analysis.

---

## 🖥️ Demo

> Launch the app and get a live valuation dashboard in seconds — adjust assumptions via sliders and watch price targets update instantly.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)
![Yahoo Finance](https://img.shields.io/badge/Yahoo%20Finance-6001D2?style=for-the-badge&logo=yahoo&logoColor=white)

---

## 📌 Features

- **Live Data** — Pulls real-time income statement, cash flow, and balance sheet data via `yfinance`
- **Historical FCFF** — Computes Free Cash Flow to Firm for all available fiscal years with CAGR
- **WACC Calculator** — Auto-computes Weighted Average Cost of Capital using CAPM; fully overridable via sliders
- **3-Scenario DCF** — Bull, Base, and Bear case price targets with upside/downside %
- **Sensitivity Table** — Color-coded heatmap of price per share across WACC × Terminal Growth Rate grid
- **Interactive Controls** — 15+ sidebar sliders to stress-test every assumption instantly
- **Excel Export** — One-click download of the full model (Historical FCFF + Scenarios + Sensitivity)

---

## 🧮 Valuation Methodology

### FCFF Formula
```
FCFF = EBIT × (1 − Tax Rate) + D&A − CapEx − ΔWWC
```

### WACC (via CAPM)
```
Ke  = Rf + β × ERP
WACC = (Ke × We) + (Kd × (1 − t) × Wd)
```

### DCF Price Target
```
Terminal Value  = FCFF₅ × (1 + g) / (WACC − g)
Enterprise Value = Σ PV(FCFFs) + PV(Terminal Value)
Price Target    = (EV − Net Debt) / Shares Outstanding
```

| Parameter | Default |
|-----------|---------|
| Risk-Free Rate (Rf) | 4.2% |
| Equity Risk Premium (ERP) | 5.5% |
| Beta (β) | 1.1 |
| Tax Rate | 22% |
| Forecast Period | 5 Years |

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/your-username/accenture-dcf.git
cd accenture-dcf
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
streamlit run accenture_dcf.py
```

The app will open automatically at `http://localhost:8501`

> **Note:** First load takes 5–15 seconds while financial data is fetched from Yahoo Finance.

---

## 📦 Requirements

```
yfinance
pandas
numpy
plotly
streamlit
openpyxl
```

Or install directly:
```bash
pip install yfinance pandas numpy plotly streamlit openpyxl
```

---

## 📁 Project Structure

```
accenture-dcf/
│
├── accenture_dcf.py      # Main application — all logic + Streamlit UI
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

---

## 📊 App Sections

| Section | Description |
|---------|-------------|
| **Company Snapshot** | Live price, market cap, P/E, EV/EBITDA |
| **Historical FCFF** | Computed FCFF for each fiscal year + CAGR |
| **WACC Breakdown** | Cost of equity, debt, weights, and final WACC |
| **Scenario Analysis** | Bull / Base / Bear price targets and upside % |
| **FCFF Projection** | 5-year projected cash flows (Base Case) |
| **Sensitivity Table** | Price matrix across WACC and terminal growth combinations |
| **Excel Export** | Download the full model as a `.xlsx` file |

---

## ⚙️ Sidebar Controls

All assumptions are adjustable in real time via the sidebar:

- **WACC Inputs** — Risk-Free Rate, Equity Risk Premium, Beta
- **Bull Case** — FCFF Growth, Terminal Growth, WACC
- **Base Case** — FCFF Growth, Terminal Growth, WACC
- **Bear Case** — FCFF Growth, Terminal Growth, WACC
- **Sensitivity Range** — WACC min/max, Terminal Growth min/max

---

## ⚠️ Important Notes

- **WACC must always be greater than the Terminal Growth Rate.** Combinations where WACC ≤ TG are displayed as `N/M` (Not Meaningful) in the sensitivity table — the Gordon Growth Model breaks down at this boundary.
- **Tax rate is fixed at 22%** to normalize historical FCFF and avoid distortion from one-time tax items.
- **Fallback FCFF of $8.6B** is used if Yahoo Finance data is unavailable (based on FY2024 actual).
- This tool is for **educational and analytical purposes only** and does not constitute investment advice.

---

## 📈 Default Scenario Assumptions

| Scenario | FCFF Growth | Terminal Growth | WACC |
|----------|-------------|-----------------|------|
| 🟢 Bull | 12% | 4.0% | 9.0% |
| 🔵 Base | 8% | 3.5% | 10.0% |
| 🔴 Bear | 3% | 2.5% | 11.5% |

---

## 🏢 About Accenture

- **Ticker:** NYSE: ACN
- **Sector:** IT Services & Consulting
- **Fiscal Year End:** August 31
- **Headquarters:** Dublin, Ireland

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

*Built with ❤️ using Python, Streamlit, and yfinance*

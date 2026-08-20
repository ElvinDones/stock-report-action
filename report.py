"""
report.py

Henter kursdata for en liste tickere og genererer en markdown-rapport
med avkastning og volatilitet siste 30 dager.

Kjøres av GitHub Actions-workflowen i .github/workflows/report.yml,
men fungerer like fint lokalt: python report.py
"""

import os
from datetime import date
import pandas as pd
import yfinance as yf

# Juster denne listen til det du vil følge med på
TICKERS = ["EQNR.OL", "DNB.OL", "NHY.OL", "AAPL", "MSFT"]

LOOKBACK_DAYS = 30


def hent_data(ticker: str) -> pd.DataFrame:
    """Henter daglige sluttkurser for en ticker."""
    hist = yf.Ticker(ticker).history(period=f"{LOOKBACK_DAYS}d")
    return hist


def beregn_nokkeltall(hist: pd.DataFrame) -> dict:
    """Beregner avkastning og volatilitet fra kurshistorikk."""
    closes = hist["Close"]
    daglig_avkastning = closes.pct_change().dropna()

    return {
        "siste_kurs": closes.iloc[-1],
        "periode_avkastning_pct": (closes.iloc[-1] / closes.iloc[0] - 1) * 100,
        "volatilitet_pct": daglig_avkastning.std() * 100,
    }


def bygg_rapport(rader: list[dict]) -> str:
    """Setter sammen markdown-tabellen og litt metadata."""
    linjer = [
        f"# Aksjerapport – {date.today().isoformat()}",
        "",
        f"Periode: siste {LOOKBACK_DAYS} handelsdager",
        "",
        "| Ticker | Siste kurs | Avkastning (%) | Volatilitet (%) |",
        "|---|---:|---:|---:|",
    ]
    for r in rader:
        linjer.append(
            f"| {r['ticker']} | {r['siste_kurs']:.2f} | "
            f"{r['periode_avkastning_pct']:+.2f} | {r['volatilitet_pct']:.2f} |"
        )
    return "\n".join(linjer) + "\n"


def bygg_html_rapport(rader: list[dict]) -> str:
    """Setter sammen en enkel, stilsatt HTML-side med samme tall som markdown-rapporten."""
    rows_html = "\n".join(
        f"""        <tr>
          <td>{r['ticker']}</td>
          <td>{r['siste_kurs']:.2f}</td>
          <td class="{'pos' if r['periode_avkastning_pct'] >= 0 else 'neg'}">{r['periode_avkastning_pct']:+.2f}%</td>
          <td>{r['volatilitet_pct']:.2f}%</td>
        </tr>"""
        for r in rader
    )

    return f"""<!DOCTYPE html>
<html lang="no">
<head>
  <meta charset="UTF-8">
  <title>Aksjerapport – {date.today().isoformat()}</title>
  <style>
    body {{
      font-family: -apple-system, Segoe UI, Roboto, sans-serif;
      background: #0d1117;
      color: #e6edf3;
      max-width: 720px;
      margin: 48px auto;
      padding: 0 16px;
    }}
    h1 {{ font-size: 1.5rem; }}
    .meta {{ color: #8b949e; margin-bottom: 24px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{
      text-align: right;
      padding: 10px 12px;
      border-bottom: 1px solid #21262d;
    }}
    th:first-child, td:first-child {{ text-align: left; }}
    th {{ color: #8b949e; font-weight: 500; font-size: 0.85rem; }}
    .pos {{ color: #3fb950; }}
    .neg {{ color: #f85149; }}
    footer {{ margin-top: 32px; color: #8b949e; font-size: 0.8rem; }}
  </style>
</head>
<body>
  <h1>Aksjerapport</h1>
  <p class="meta">{date.today().isoformat()} · siste {LOOKBACK_DAYS} handelsdager</p>
  <table>
    <thead>
      <tr><th>Ticker</th><th>Siste kurs</th><th>Avkastning</th><th>Volatilitet</th></tr>
    </thead>
    <tbody>
{rows_html}
    </tbody>
  </table>
  <footer>Generert automatisk av GitHub Actions.</footer>
</body>
</html>
"""


def main():
    rader = []
    for ticker in TICKERS:
        try:
            hist = hent_data(ticker)
            if hist.empty:
                print(f"Advarsel: ingen data for {ticker}, hopper over")
                continue
            nokkeltall = beregn_nokkeltall(hist)
            rader.append({"ticker": ticker, **nokkeltall})
        except Exception as e:
            print(f"Feil ved henting av {ticker}: {e}")

    rapport = bygg_rapport(rader)
    html_rapport = bygg_html_rapport(rader)

    # Opprett mappene hvis de ikke finnes (Git lagrer ikke tomme mapper)
    os.makedirs("reports", exist_ok=True)
    os.makedirs("docs", exist_ok=True)

    # Skriv dagens rapport + oppdater "latest" som alltid peker på siste kjøring
    with open(f"reports/{date.today().isoformat()}.md", "w") as f:
        f.write(rapport)
    with open("reports/latest.md", "w") as f:
        f.write(rapport)

    # docs/index.html er siden GitHub Pages serverer
    with open("docs/index.html", "w") as f:
        f.write(html_rapport)

    print(rapport)


if __name__ == "__main__":
    main()

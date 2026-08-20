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

    # Opprett reports/-mappa hvis den ikke finnes (Git lagrer ikke tomme mapper)
    os.makedirs("reports", exist_ok=True)

    # Skriv dagens rapport + oppdater "latest" som alltid peker på siste kjøring
    with open(f"reports/{date.today().isoformat()}.md", "w") as f:
        f.write(rapport)
    with open("reports/latest.md", "w") as f:
        f.write(rapport)

    print(rapport)


if __name__ == "__main__":
    main()

import yfinance as yf
import pandas as pd

symbol = "AAPL"
df = yf.download(
    symbol,
    start="2022-01-01",
    end="2024-12-31",
    interval="1d",
    auto_adjust=False
)

df = df.reset_index()
df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]

df.columns = ["date", "open", "high", "low", "close", "volume"]
df["date"] = pd.to_datetime(df["date"], utc=True)

df.to_csv("AAPL-1d.csv", index=False)

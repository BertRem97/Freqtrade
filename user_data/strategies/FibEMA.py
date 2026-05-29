# --- Fibonacci EMA Strategy for Freqtrade ---
# Uses EMA8, EMA13, EMA21, EMA34, EMA55, EMA89, EMA144
# Buy: bullish cross of EMA8 > EMA13
# Sell: bearish cross of EMA8 < EMA13

from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class FibEMA(IStrategy):
    # Timeframe
    timeframe = "15m"

    # Minimal ROI
    minimal_roi = {
        "0": 0.059,
        "10": 0.026,
        "41": 0.012,
        "114": 0
    }

    stoploss = -0.05

    # Strategy startup candles
    startup_candle_count = 150

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Fibonacci EMA sequence
        fibonacci_emas = [8, 13, 21, 34, 55, 89, 144]

        # Generate EMAs
        for period in fibonacci_emas:
            dataframe[f"ema_{period}"] = ta.EMA(dataframe, timeperiod=period)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Buy when EMA8 crosses above EMA13 + trend is upwards
        dataframe.loc[
            (
                (dataframe["ema_8"] > dataframe["ema_13"]) &
                (dataframe["ema_13"] > dataframe["ema_21"]) &
                (dataframe["ema_21"] > dataframe["ema_34"]) &
                (dataframe["ema_34"] > dataframe["ema_55"]) &
                (dataframe["volume"] > 0)
            ),
            "buy"
        ] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Sell when EMA8 crosses below EMA13
        dataframe.loc[
            (
                (dataframe["ema_8"] < dataframe["ema_13"]) &
                (dataframe["ema_13"] < dataframe["ema_21"]) &
                (dataframe["volume"] > 0)
            ),
            "sell"
        ] = 1
        return dataframe

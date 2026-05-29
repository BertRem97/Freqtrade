from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class DynamicLong_Short(IStrategy):
    #maakt gebruik van EMA20, 200, RSI en ATR
    # =====================
    # Algemene instellingen
    # =====================
    timeframe = "15m"
    can_short = True
    startup_candle_count = 200

    # ROI praktisch uitgeschakeld
    minimal_roi = {
        "0": 100
    }

    stoploss = -0.30  # noodstop, echte exits via custom_exit

    trailing_stop = False
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = True

    # =====================
    # Indicatoren
    # =====================
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)

        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)

        return dataframe

    # =====================
    # Entries
    # =====================
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        # -------- LONG --------
        dataframe.loc[
            (
                (dataframe["ema50"] > dataframe["ema200"]) &      # uptrend
                (dataframe["close"] < dataframe["ema50"]) &       # pullback
                (dataframe["rsi"] < 40) &                          # oversold
                (dataframe["volume"] > 0)
            ),
            "enter_long"
        ] = 1

        # -------- SHORT --------
        dataframe.loc[
            (
                (dataframe["ema50"] < dataframe["ema200"]) &      # downtrend
                (dataframe["close"] > dataframe["ema50"]) &       # pullback
                (dataframe["rsi"] > 60) &                          # overbought
                (dataframe["volume"] > 0)
            ),
            "enter_short"
        ] = 1

        return dataframe

    # =====================
    # Exit signals (primair)
    # =====================
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        # LONG exit: momentum of trend verliest kracht
        dataframe.loc[
            (
                (dataframe["rsi"] > 70) |
                (dataframe["ema50"] < dataframe["ema200"])
            ),
            "exit_long"
        ] = 1

        # SHORT exit: momentum of trend verliest kracht
        dataframe.loc[
            (
                (dataframe["rsi"] < 30) |
                (dataframe["ema50"] > dataframe["ema200"])
            ),
            "exit_short"
        ] = 1

        return dataframe

    # =====================
    # ATR Dynamic Exit (secundair, profit-aware)
    # =====================
    def custom_exit(
     self,
     pair: str,
     trade,
     current_time,
     current_rate,
     current_profit,
     **kwargs
 ):

     # ATR pas actief NA winst (winrate-bescherming)
     if current_profit < 0.015:
         return None

     dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
     last = dataframe.iloc[-1]

     atr = last["atr"]
     atr_multiplier = 1.3

     # -------- LONG --------
     if trade.entry_side == "long":
         atr_stop_price = trade.open_rate + (atr * atr_multiplier)
         if current_rate < atr_stop_price:
             return "atr_dynamic_exit_long"

     # -------- SHORT --------
     if trade.entry_side == "short":
         atr_stop_price = trade.open_rate - (atr * atr_multiplier)
         if current_rate > atr_stop_price:
             return "atr_dynamic_exit_short"

     # -------- Time-based kill --------
     if trade.open_duration > 240 and current_profit < 0.01:
         return "time_exit"

     return None


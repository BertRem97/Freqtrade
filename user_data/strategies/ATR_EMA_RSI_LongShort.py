from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


class ATR_EMA_RSI_LongShort(IStrategy):

    # =====================
    # Freqtrade instellingen
    # =====================
    timeframe = '15m'
    can_short = True

    startup_candle_count = 200

    # ROI & stoploss (basis, exits gebeuren vooral via signalen)
    minimal_roi = {
        "0": 0.10,
        "30": 0.05,
        "60": 0.02
    }

    stoploss = -0.05 # harde noodstop

    trailing_stop = False

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # =====================
    # Indicatoren
    # =====================
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        # Trend
        dataframe['ema50'] = ta.EMA(dataframe, timeperiod=50)
        dataframe['ema200'] = ta.EMA(dataframe, timeperiod=200)

        # Momentum
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)

        # Volatiliteit
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)

        return dataframe

    # =====================
    # LONG ENTRY
    # =====================
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        # Long = uptrend + pullback + oversold momentum
        dataframe.loc[
            (
                (dataframe['ema50'] > dataframe['ema200']) &
                (dataframe['close'] < dataframe['ema50']) &
                (dataframe['rsi'] < 40) &
                (dataframe['volume'] > 0)
            ),
            'enter_long'
        ] = 1

        # Short = downtrend + pullback + overbought momentum
        dataframe.loc[
            (
                (dataframe['ema50'] < dataframe['ema200']) &
                (dataframe['close'] > dataframe['ema50']) &
                (dataframe['rsi'] > 60) &
                (dataframe['volume'] > 0)
            ),
            'enter_short'
        ] = 1

        return dataframe

    # =====================
    # EXIT
    # =====================
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        # Exit long bij trendverlies of momentum omkering
        dataframe.loc[
            (
                (dataframe['ema50'] < dataframe['ema200']) |
                (dataframe['rsi'] > 70)
            ),
            'exit_long'
        ] = 1

        # Exit short bij trendverlies of momentum omkering
        dataframe.loc[
            (
                (dataframe['ema50'] > dataframe['ema200']) |
                (dataframe['rsi'] < 30)
            ),
            'exit_short'
        ] = 1

        return dataframe

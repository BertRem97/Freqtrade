from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
import technical.indicators as ftt
from functools import reduce

from freqtrade.strategy import (
    IntParameter,
    DecimalParameter,
    CategoricalParameter
)


class ichi(IStrategy):

    INTERFACE_VERSION = 3
    can_short = True

    # =========================
    # CORE SETTINGS
    # =========================
    timeframe = '1h'
    startup_candle_count = 96
    process_only_new_candles = False

    minimal_roi = {
        "0": 0.56,
        "377": 0.234,
        "638": 0.085,
        "1751": 0
        }

    stoploss = -0.202

    trailing_stop = True
    trailing_only_offset_is_reached = False
    trailing_stop_positive = 0.0222
    trailing_stop_positive_offset = 0.227


    # =========================
    # BUY SPACE
    # =========================
    buy_trend_above_senkou_level = 6
    buy_trend_bullish_level = 8
    buy_fan_shift = 4

    buy_min_gain = 1.003

    # =========================
    # SELL SPACE
    # =========================
    sell_trend_indicator = "trend_close_15m"

    # =========================
    # INDICATORS
    # =========================
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        heikinashi = qtpylib.heikinashi(dataframe)

        dataframe['open'] = heikinashi['open']
        dataframe['high'] = heikinashi['high']
        dataframe['low'] = heikinashi['low']

        dataframe['trend_close_5m'] = dataframe['close']
        dataframe['trend_close_15m'] = ta.EMA(dataframe['close'], 3)
        dataframe['trend_close_30m'] = ta.EMA(dataframe['close'], 6)
        dataframe['trend_close_1h'] = ta.EMA(dataframe['close'], 12)
        dataframe['trend_close_2h'] = ta.EMA(dataframe['close'], 24)
        dataframe['trend_close_4h'] = ta.EMA(dataframe['close'], 48)
        dataframe['trend_close_6h'] = ta.EMA(dataframe['close'], 72)
        dataframe['trend_close_8h'] = ta.EMA(dataframe['close'], 96)

        dataframe['trend_open_5m'] = dataframe['open']
        dataframe['trend_open_15m'] = ta.EMA(dataframe['open'], 3)
        dataframe['trend_open_30m'] = ta.EMA(dataframe['open'], 6)
        dataframe['trend_open_1h'] = ta.EMA(dataframe['open'], 12)
        dataframe['trend_open_2h'] = ta.EMA(dataframe['open'], 24)
        dataframe['trend_open_4h'] = ta.EMA(dataframe['open'], 48)
        dataframe['trend_open_6h'] = ta.EMA(dataframe['open'], 72)
        dataframe['trend_open_8h'] = ta.EMA(dataframe['open'], 96)

        dataframe['fan_magnitude'] = dataframe['trend_close_1h'] / dataframe['trend_close_8h']
        dataframe['fan_gain'] = dataframe['fan_magnitude'] / dataframe['fan_magnitude'].shift(1)

        ichimoku = ftt.ichimoku(
            dataframe,
            conversion_line_period=20,
            base_line_periods=60,
            laggin_span=120,
            displacement=30
        )

        dataframe['senkou_a'] = ichimoku['senkou_span_a']
        dataframe['senkou_b'] = ichimoku['senkou_span_b']

        return dataframe

    # =========================
    # ENTRY (LONG + SHORT)
    # =========================
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        level = self.buy_trend_above_senkou_level
        bull = self.buy_trend_bullish_level
        shift = self.buy_fan_shift
        gain = self.buy_min_gain

        conditions = []

        # LONG
        if level >= 1:
            conditions += [
                dataframe['trend_close_5m'] > dataframe['senkou_a'],
                dataframe['trend_close_5m'] > dataframe['senkou_b']
            ]

        if bull >= 1:
            conditions.append(dataframe['trend_close_5m'] > dataframe['trend_open_5m'])

        conditions += [
            dataframe['fan_gain'] >= gain,
            dataframe['fan_magnitude'] > 1
        ]

        for x in range(shift):
            conditions.append(
                dataframe['fan_magnitude'].shift(x + 1) < dataframe['fan_magnitude']
            )

        if conditions:
            dataframe.loc[
                reduce(lambda a, b: a & b, conditions),
                "enter_long"
            ] = 1

        # =========================
        # SHORT
        # =========================
        short_conditions = []

        if level >= 1:
            short_conditions += [
                dataframe['trend_close_5m'] < dataframe['senkou_a'],
                dataframe['trend_close_5m'] < dataframe['senkou_b']
            ]

        short_conditions += [
            dataframe['fan_magnitude'] < 1,
            dataframe['fan_gain'] <= (2 - gain)
        ]

        for x in range(shift):
            short_conditions.append(
                dataframe['fan_magnitude'].shift(x + 1) > dataframe['fan_magnitude']
            )

        if short_conditions:
            dataframe.loc[
                reduce(lambda a, b: a & b, short_conditions),
                "enter_short"
            ] = 1

        return dataframe

    # =========================
    # EXIT
    # =========================
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        ind = self.sell_trend_indicator

        dataframe.loc[
            qtpylib.crossed_below(dataframe['trend_close_5m'], dataframe[ind]),
            "exit_long"
        ] = 1

        dataframe.loc[
            qtpylib.crossed_above(dataframe['trend_close_5m'], dataframe[ind]),
            "exit_short"
        ] = 1

        return dataframe
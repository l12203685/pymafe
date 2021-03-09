import pandas as pd
import numpy as np

def ma_cross(ohlc, w_1=5, w_2=20, w_3=60):
    sma_1 = ohlc['close'].rolling(w_1).mean()
    sma_2 = ohlc['close'].rolling(w_2).mean()
    sma_3 = ohlc['close'].rolling(w_3).mean()

    cond_LE = (
        (sma_1 >= sma_2) & (sma_1.shift() < sma_2.shift())
        #    & (ohlc['close'] > sma_3)
    ).shift().fillna(False)

    cond_LX = (
        ((sma_1 < sma_2) & (sma_1.shift() >= sma_2.shift()))
        #    | (ohlc['close'] < sma_3)
    ).shift().fillna(False)

    LE = cond_LE[cond_LE].index
    LX = cond_LX[cond_LX].index
    LX = [LX[LE[i] <= LX][0] for i in range(len(LE) - 1)]

    LEX = pd.DataFrame({
        'LE': pd.Series(LE),
        'LX': pd.Series(LX),
    }).dropna()

    return LEX, cond_LE, cond_LX

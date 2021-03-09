# pymafe

A Trading Strategy Analysis Tool


```python
from pymafe import pymafe
import pandas as pd

## 黃金死亡交叉策略
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


stock_code = '0050'
api = StockDataAPI(stock_code)
ohlc = api.get_ohlc()
LEX, cond_LE, cond_LX = ma_cross(ohlc)
entry = LEX['LE']
exit = LEX['LX']
long_short = 'L'


lex, cond_le, cond_lx = ma_cross(ohlc)
entry = lex['LE']
eexit = lex['LX']
ls = 'L'

print(lex)
mafe = pymafe.MAFE(
    ohlc,
    entry=LEX['LE'],
    exit=LEX['LX'],
    long_or_short='Long'
)


mafe_data = mafe.eda()
print(mafe_data)
```

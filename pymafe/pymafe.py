import pandas as pd
import numpy as np


class MAFE():

    def __init__(
        self,
        ohlc: pd.DataFrame,
        entry: pd.Series,
        exit: pd.Series,
        long_or_short: str
        #atr_window: int,
        #trading_cost: 0.005 (0.5%)
    ):

        self.atr_window = 20
        self._hist_bins = 20
        self.trading_cost = 0.5/1000
        self.long_short = 'S' if ('s' in long_or_short) or (
            'S' in long_or_short) else 'L'
        self.ohlc = ohlc
        self.entry = entry
        self.exit = exit
        self.tr = pd.DataFrame({
            'ch': (ohlc['close'].shift() - ohlc['high']).abs(),
            'cl': (ohlc['close'].shift() - ohlc['low']).abs(),
            'hl': (ohlc['high'] - ohlc['low']),
        }).max(axis=1)

        self.atr = self.tr.rolling(self.atr_window).mean()
        self.atr_entry = self.atr[entry].reset_index(drop=True)
        #self.data = pd.DataFrame();
        self.data = pd.DataFrame({
            'PnL': self._pnl(),
            'MAE': pd.Series(self._mae(0)),
            'MFE': pd.Series(self._mfe(1)),
            'cMFE': pd.Series(self._mfe(0)),
            'MHL': self._mhl(),
        }).fillna(0)

        self.data['WL'] = (self.data['PnL'] > 0).astype(
            int).replace({1: 'W', 0: 'L'})
        self.data['ATR'] = self.atr_entry

    def _pnl(self):
        ohlc = self.ohlc
        entry = self.entry
        exit = self.exit
        long_short = self.long_short
        trading_cost = self.trading_cost
        entry_price = ohlc.loc[entry]['open'].reset_index(drop=True)
        exit_price = ohlc.loc[exit]['open'].reset_index(drop=True)
        return (
            (exit_price - entry_price - trading_cost *
             (exit_price + entry_price).abs()/2) * int(long_short == 'L')
            + (- exit_price + entry_price - trading_cost *
               (exit_price + entry_price).abs()/2) * int(long_short == 'S')
        ).rename('PnL')

    def _ae(self):
        ohlc = self.ohlc
        entry = self.entry
        exit = self.exit
        long_short = self.long_short
        trading_cost = self.trading_cost
        return {
            td:
            # if long entry
            (- ohlc.loc[entry].iloc[td]['open']
             + ohlc[(ohlc.index >= entry.iloc[td]) &
                    (ohlc.index <= exit.iloc[td])]['low']
             - trading_cost * ohlc.loc[entry].iloc[td]['open']
             ).apply(lambda x: min(0, x)) * int(long_short == 'L') * -1
            +
            # if short entry
            (+ ohlc.loc[entry].iloc[td]['open']
             - ohlc[(ohlc.index >= entry.iloc[td]) &
                    (ohlc.index <= exit.iloc[td])]['high']
             - trading_cost * ohlc.loc[entry].iloc[td]['open']
             ).apply(lambda x: min(0, x)) * int(long_short == 'S') * -1
            for td in range(len(entry))
        }

    def _fe(self):
        ohlc = self.ohlc
        entry = self.entry
        exit = self.exit
        long_short = self.long_short
        trading_cost = self.trading_cost
        return {
            td:
            # if long entry
            (- ohlc.loc[entry].iloc[td]['open']
             + ohlc[(ohlc.index >= entry.iloc[td]) &
                    (ohlc.index <= exit.iloc[td])]['high']
             - trading_cost * ohlc.loc[entry].iloc[td]['open']
             ).apply(lambda x: max(0, x)) * int(long_short == 'L')
            +
            # if short entry
            (+ ohlc.loc[entry].iloc[td]['open']
             - ohlc[(ohlc.index >= entry.iloc[td]) &
                    (ohlc.index <= exit.iloc[td])]['low']
             - trading_cost * ohlc.loc[entry].iloc[td]['open']
             ).apply(lambda x: max(0, x)) * int(long_short == 'S')
            for td in range(len(entry))
        }

    def _fe_lv(self, td, lv):
        try:
            if lv == 0:
                return self._fe()[td].dropna()
            if lv > 0:
                mae_time = self._ae_lv(
                    td, lv - 1).rank(method='dense', ascending=False).sort_values().index[lv - 1]
                return self._fe()[td][mafe._fe()[td].index < mae_time].dropna()
        except:
            return self._fe()[td].dropna().iloc[0]

    def _ae_lv(self, td, lv):
        try:
            if lv == 0:
                return self._ae()[td].dropna()
            if lv > 0:
                mfe_time = self._fe_lv(
                    td, lv - 1).rank(method='dense', ascending=False).sort_values().index[lv - 1]
                return self._ae()[td][mafe._ae()[td].index < mfe_time].dropna()
        except:
            return self._ae()[td].dropna().iloc[0]

    def _mae(self, lv=0):
        return {td: self._ae_lv(td, lv).max() for td in range(len(self.entry))}

    def _mfe(self, lv=0):
        return {td: self._fe_lv(td, lv).max() for td in range(len(self.entry))}

    def _hl(self):
        ohlc = self.ohlc
        entry = self.entry
        exit = self.exit
        long_short = self.long_short

        return {
            td:
            ((ohlc[(ohlc.index >= entry[td]) & (ohlc.index <= exit[td])]['high']
              - ohlc[(ohlc.index >= entry[td]) & (ohlc.index <= exit[td])]['low']).cummax()
             -
             (ohlc[(ohlc.index >= entry[td]) & (ohlc.index <= exit[td])]['high']
              - ohlc[(ohlc.index >= entry[td]) & (ohlc.index <= exit[td])]['low'])) * int(long_short == 'L')
            +
            ((ohlc[(ohlc.index >= entry[td]) & (ohlc.index <= exit[td])]['low']
              - ohlc[(ohlc.index >= entry[td]) & (ohlc.index <= exit[td])]['high']).cummax()
             -
             (ohlc[(ohlc.index >= entry[td]) & (ohlc.index <= exit[td])]['low']
              - ohlc[(ohlc.index >= entry[td]) & (ohlc.index <= exit[td])]['high'])) * int(long_short == 'S')
            for td in range(len(entry))
        }

    def _mhl(self, lv=0):
        return {td: hl.max() for td, hl in self._hl().items()}

    def _hist(self):
        data = self.data
        data[['PnL', 'MAE', 'MFE']].hist(bins=self._hist_bins)

    def _mae_hist(self):
        data = self.data
        data[data['WL'] == 'W']['MAE'].hist(
            bins=self._hist_bins, color='r', alpha=0.6, rwidth=0.7, orientation='horizontal')
        data[data['WL'] == 'L']['MAE'].hist(
            bins=self._hist_bins, color='g', alpha=0.6, rwidth=0.7, orientation='horizontal')

    def _mfe_hist(self):
        data = self.data
        data[data['WL'] == 'W']['MFE'].hist(
            bins=self._hist_bins, color='r', alpha=0.6, rwidth=0.7, orientation='horizontal')
        data[data['WL'] == 'L']['MFE'].hist(
            bins=self._hist_bins, color='g', alpha=0.6, rwidth=0.7, orientation='horizontal')

    def _mhl_hist(self):
        data = self.data
        data[data['WL'] == 'W']['MHL'].hist(
            bins=self._hist_bins, color='r', alpha=0.6, rwidth=0.7, orientation='horizontal')
        data[data['WL'] == 'L']['MHL'].hist(
            bins=self._hist_bins, color='g', alpha=0.6, rwidth=0.7, orientation='horizontal')

    def _scatter(self):
        data = self.data
        data.plot.scatter(x='PnL', y='MAE')
        data.plot.scatter(x='PnL', y='MFE')
        data.plot.scatter(x='MAE', y='MFE')

    def _time_series(self):
        data = self.data
        data[['PnL', 'MAE', 'MFE']].plot()
        data['ATR'].plot(secondary_y=True)

    def eda(self):  # Exploratory Data Analysis
        data = self.data

        print(data.describe())

        self._time_series()
        self._scatter()
        self._hist()
        self._mae_hist()
        self._mfe_hist()
        self._mhl_hist()

        return data
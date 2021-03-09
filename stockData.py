import pandas as pd
import numpy as np
import os
import sys
import requests
import json
from datetime import datetime, timedelta

class StockDataAPI():
    
    def __init__(
            self, 
            stock_code: str, 
            start: datetime=datetime(2010, 1, 1), 
            end: datetime=datetime.now(),
            ):
        self.now = datetime.now();
        self.stock_code = str(stock_code);
        self.start = start; 
        self.end = end;

    def get_fin_data(self):
    
        def get_data(stock_code, start, end):
    
            url = ('https://statementdog.com/api/v1/fundamentals/' + str(stock_code) + '/' 
               + str(start.year) + '/' + str(int(start.month/4 + 1)) + '/'
               + str(end.year) + '/' + str(int(end.month/4 + 1)) + '/'
               + 'cf?qub=true&qf=analysis');
            
            res = requests.get(url);
            
            return res.json()
        
        def _parse_data(data, freq):
            _data_dict = {};
            for key, value in data[freq].items():
                try:
                    _data_dict[value['label']] = (
                        pd.DataFrame(value['data'], columns=['index', key])[key]
                        );
                except:
                    None
            
            return pd.DataFrame(_data_dict);
        
        # monthly data
        def _data_m(data):
            
            df = _parse_data(data, 'monthly');
            ori_columns = list(df.columns);
            df['date'] = (
                pd.DataFrame(data['common']['TimeM']['data'])[1]
                .astype(str)
                .apply(lambda x: 
                       (datetime(int(x[:4]), (int(x[-2:]) + 1), 1) if x[-2:] != '12' 
                        else datetime(int(x[:4]) + 1, 1, 1))
                       - timedelta(1))
                );
            ticker_name = data['common']['StockInfo']['data']['ticker_name'];
            df['stock_code'] = ticker_name.split(' ')[0];
            df['stock_name'] = ticker_name.split(' ')[1];
            
            return (df[['stock_code', 'stock_name', 'date'] + ori_columns]
                    .dropna(how='all', axis=1).replace('無', np.nan))
        
        # quarterly data
        def _data_q(data):
            
            df = _parse_data(data, 'quarterly');
            ori_columns = list(df.columns);
            df['date'] = (
                pd.DataFrame(data['common']['TimeQ']['data'])[1]
                .astype(str)
                .apply(lambda x: 
                       (datetime(int(x[:4]), (int(x[-1:]) * 3 + 1), 1) if x[-1:] != '4' 
                        else datetime(int(x[:4]) + 1, 1, 1))
                       - timedelta(1))
                );
            
            ticker_name = data['common']['StockInfo']['data']['ticker_name'];
            df['stock_code'] = ticker_name.split(' ')[0];
            df['stock_name'] = ticker_name.split(' ')[1];
            
            return (df[['stock_code', 'stock_name', 'date'] + ori_columns]
                    .dropna(how='all', axis=1).replace('無', np.nan))
        
        # yearly data
        def _data_y(data):
            
            df = _parse_data(data, 'yearly');
            ori_columns = list(df.columns);
            df['date'] = (
                pd.DataFrame(data['common']['TimeY']['data'])[1].astype(str)
                .apply(lambda x: datetime(int(x[:4]), 12, 31)));
            
            ticker_name = data['common']['StockInfo']['data']['ticker_name'];
            df['stock_code'] = ticker_name.split(' ')[0];
            df['stock_name'] = ticker_name.split(' ')[1];
            
            return (df[['stock_code', 'stock_name', 'date'] + ori_columns]
                    .dropna(how='all', axis=1).replace('無', np.nan))
        
        data = get_data(self.stock_code, self.start, self.end);
        
        return _data_m(data).set_index('date'), _data_q(data).set_index('date'), _data_y(data).set_index('date')
    
    def get_info(self):
        stock_code = self.stock_code;
        from bs4 import BeautifulSoup as bs
        url = 'https://concords.moneydj.com/z/zc/zca/zca_' + stock_code + '.djhtm';
        res = requests.get(url);
        soup = bs(res.text)
        column_map = {};
        value_map = {};
        content_map = {};
        i = 0;
        for sub_soup in soup.select("td tr tr"):
            column_map[i] = [string.text for string in sub_soup.select(".t4t1")];
            value_map[i] = [string.text for string in sub_soup.select(".t3n1")];
            content_map[i] = [string.text for string in sub_soup.select(".t3t1")];
            i += 1;
        for column_list in column_map.values():
            for value_list in value_map.values():
                content = {
                    key: value 
                    for key in column_list
                    for value in value_list};
        content = pd.concat(
            [pd.Series(column_map).astype(str), 
            pd.Series(value_map), 
            pd.Series(content_map).astype(str)
            ], axis=1)
        content = content.set_index(0);
        content = pd.concat(
            [content[content[1].apply(lambda x: len(x) != 0)][1], 
            content[content[1].apply(lambda x: len(x) == 0)][2]
            ], axis=0);
        content = content[content.index != '[]'];
        return content
    
    def _get_info(self):

        stock_code = self.stock_code;

        def _info(stock_code):
            url = 'https://marketinfo.api.cnyes.com/mi/api/v1/TWS:' + stock_code + ':STOCK/info'
            res = requests.get(url)
            data = pd.Series(res.json()['data'])
            return data

        def _profile(stock_code):
            url = 'https://ws.api.cnyes.com/ws/api/v1/quote/quotes/TWS:' + stock_code + ':STOCK?column=I';
            res = requests.get(url);
            data = res.json()['data'];
            mapping = {
                '0': 'ticker',
                '6': 'close',
                '11': 'price_change',
                '12': 'day_high',
                '13': 'day_low',
                '19': 'open',
                '21': 'last_close',
                '56': 'price_change_pct',
                '3265': '1_year_high',
                '3266': '1_year_low',
                '200007': 'date',
                '200009': 'stock_name',
                '200010': 'stock_code',
                '200024': 'stock_name_eng',
                '700001': 'pe_ratio',
                '700005': 'market_value',
                '700006': 'pb_ratio',
                '800001': 'trading_volume',
                '800013': 'ticker_2',
            }
            data = pd.Series(data[0]);
            data.index = pd.Series(data.index).replace(mapping);
            data = data.sort_index();

            return data
        
        return pd.concat([_info(stock_code), _profile(stock_code)], sort=False)

    def get_ohlc(self, freq='D'):
        stock_code = self.stock_code;
        url_domain = 'https://ws.api.cnyes.com/ws/api/v1/charting/history';
        end = datetime(self.now.year, self.now.month, self.now.day);
        start = end - timedelta(365 * 20);
        url = (
            url_domain + 
            '?resolution=D' + #freq + 
            '&symbol=TWS:' + stock_code + ':STOCK' + 
            '&from=' + str(int(end.timestamp())) + 
            '&to=' + str(int(start.timestamp())) +
            '&quote=1'
            );
        res = requests.get(url);
        data = res.json()['data'];
        df = pd.DataFrame({
            'open': data['o'],
            'high': data['h'],
            'low': data['l'],
            'close': data['c'],
            'volume': data['v']}, 
            index=pd.Series(data['t']).apply(
                lambda x: datetime.fromtimestamp(x) + 
                (timedelta(8/24) if freq == '1' else timedelta(0))
                )
            );
        df = df.resample(freq).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            }).dropna();
        return df[['open', 'high', 'low', 'close', 'volume']]
    
    def get_ohlc_std(self):
        stock_code = self.stock_code;
        df = self.get_ohlc(stock_code);
        df['volume'] = df['volume'] * 1000 * df['close'];
        df[['open', 'high', 'low', 'close']] = (
            df[['open', 'high', 'low', 'close']]/df['open'].iloc[0] * 10);
        return df

    def plot_kchart(self, start=None, end=None, freq: str='D', volume_on: bool=True, save_graph: bool=False, graph_style: str='nightclouds'):
        
        import mplfinance as mpf
        
        title = str(self.stock_code);

        if end == None:
            end = datetime(self.now.year, self.now.month, self.now.day);
        
        if start == None:
            start = end - timedelta(365 * 20);

        ohlc_data = self.get_ohlc(freq=freq);
        ohlc_data = ohlc_data[(ohlc_data.index >= start) & (ohlc_data.index <= end)];
        
        """
        Parameters
        ----------         
        volume_on : bool, optional
            draw volume or not. The default is True.
            
        graph_style : str, optional
            ohlc graph style. ['binance', 'blueskies', 'brasil', 'charles', 
            'checkers', 'classic', 'default', 'mike', 'nightclouds', 
            'sas', 'starsandstripes', 'yahoo'] are available styles
            
        Returns
        -------
        freq ohlc dataframe.
        """

        if 'volume' not in ohlc_data.columns:
            volume_on = False;
        if title == None:
            title = ohlc_data.index.max().strftime('%Y-%m-%d');
        
        market_colors = mpf.make_marketcolors(# 设置marketcolors
            up='red', down='white', edge='i', # edge:K线线柱边缘颜色(i代表继承自up和down的颜色)
            wick={'up':'red', 'down':'white'}, # wick:灯芯(上下影线)颜色
            volume='in', inherit=True, # # volume:成交量直方图的颜色 inherit:是否继承，选填
            );
        
        mpf_graph_style = mpf.make_mpf_style( # 设置图形风格
            base_mpf_style=graph_style, marketcolors=market_colors, #mpf.available_styles()
            y_on_right=True, # y_on_right:设置y轴位置是否在右
            gridaxis='both', gridstyle=':', # gridaxis:设置网格线位置 # gridstyle:设置网格线线型
            );
        
        kwargs = dict( # 设置基本参数
            type='candle', # type:绘制图形的类型，有candle, renko, ohlc, line等	
            volume=volume_on, # volume:布尔类型，设置是否显示成交量，默认False
            title=title, # title:设置标题
            ylabel='ohlc', ylabel_lower='volume', # y_label_lower:设置成交量图一栏的标题
            figscale=1, # figscale:设置图形尺寸(数值越大图像质量越高)
            figratio=(16, 9), # figratio:设置图形纵横比
            );
        if save_graph:
            plt.rcParams['font.size'] = 48;
            plt.rcParams['figure.figsize'] = (108, 72); #plot_size;
            plt.rcParams['grid.linestyle'] = ':';
            plt.rcParams['grid.linewidth'] = 3;
            plt.close();
            mpf.plot(data=kline_data, style=mpf_graph_style, **kwargs, 
                    savefig=os.path.join(file_path, 'kline', title + '.jpg'));
            plt_setting();
        if ~save_graph:
            mpf.plot(data=kline_data, style=mpf_graph_style, **kwargs)

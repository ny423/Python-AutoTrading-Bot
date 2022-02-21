import requests
import numpy as np
import pandas as pd
import talib
import config
from binance.enums import *
from binance.client import Client

pd.set_option('expand_frame_repr', False)

BASE_URL = 'http://api.binance.com'
kline = '/api/v3/klines'
TIME_INTERVAL = KLINE_INTERVAL_1HOUR
client = Client(config.Real_key, config.Real_secret)


class product:
    def __init__(self, product_name1, product_name2, time_interval=KLINE_INTERVAL_1HOUR,
                 limit=1, sma1=5, sma2=200):
        self.sma1 = sma1
        self.sma2 = sma2
        self.bought = False
        self.product_name1 = str(product_name1).upper()
        self.product_name2 = str(product_name2).upper()
        self.name = str(product_name1+product_name2).upper()
        if float(client.get_asset_balance(asset=self.product_name1)['free']) > 0:
            self.bought = True
        self.time_interval = time_interval
        self.url = self.get_url(limit=1)
        response = requests.get(self.get_url(limit=200))
        data = response.json()
        self.df = pd.DataFrame(data, columns=['open_time', 'open', 'high', 'low', 'close', 'volume',
                                             'a', 'b', 'c', 'd', 'e', 'f'])
        self.df.drop(['a', 'b', 'c', 'd', 'e', 'f'], axis=1, inplace=True)
        self.trade_count = 0
        # self.trade_record = pd.DataFrame()

    def pop_first_data(self):
        self.df.drop(axis=0, labels=0, inplace=True)
        self.df.reset_index(drop=True, inplace=True)

    def get_url(self, limit):
        return f'{BASE_URL}{kline}?symbol={self.name}&interval={self.time_interval}&limit={str(limit)}'

    def print_url(self):
        print(self.url)

    def print_df(self):
        print(self.name)
        print(self.df)
        print()

    def bought_status(self):
        return self.bought

    def import_ticket_data(self):
        response = requests.get(self.url)
        data = response.json()
        df_new = pd.DataFrame(data, columns=['open_time', 'open', 'high', 'low', 'close', 'volume',
                                             'a', 'b', 'c', 'd', 'e', 'f'])
        df_new.drop(['a', 'b', 'c', 'd', 'e', 'f'], axis=1, inplace=True)
        self.df = self.df.append(df_new)
        self.df.drop_duplicates(subset=['open_time'], inplace=True, keep='last')
        self.df.reset_index(drop=True, inplace=True)

    def negate_bought(self):
        if self.bought is False:
            self.bought = True
        else:
            self.bought = False

    # def create_bolling_band20(self):
    #     upper, middle, lower = talib.BBANDS(self.df['close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    #     self.df['upper'] = upper
    #     self.df['lower'] = lower

    def create_smas(self):
        self.df[f'sma{self.sma1}'] = talib.SMA(self.df['close'], timeperiod=self.sma1)
        self.df[f'sma{self.sma2}'] = talib.SMA(self.df['close'], timeperiod=self.sma2)

    def create_buy_sell_zone(self):
        self.df['close'] = self.df['close'].astype('float')
        # self.df.loc[(self.df['close'] < self.df['lower']), 'buy zone'] = True
        # self.df.loc[(self.df['close'] > self.df['upper']), 'sell zone'] = True
        self.df.loc[(self.df[f'sma{self.sma1}'] >= self.df[f'sma{self.sma2}']), 'buy zone'] = True
        self.df.loc[(self.df[f'sma{self.sma2}'] > self.df[f'sma{self.sma1}']), 'sell zone'] = True
        self.df['buy zone'].replace(np.nan, False, inplace=True)
        self.df['sell zone'].replace(np.nan, False, inplace=True)

    def decide_to_buy(self):
        prev_is_buy_zone = self.df['buy zone'].iloc[-2]
        current_is_buy_zone = self.df['buy zone'].iloc[-1]
        if current_is_buy_zone is True and prev_is_buy_zone is False:
            return True
        return False

    def decide_to_sell(self):
        prev_is_sell_zone = self.df['sell zone'].iloc[-2]
        current_is_sell_zone = self.df['sell zone'].iloc[-1]
        if current_is_sell_zone is True and prev_is_sell_zone is False:
            return True
        return False

    def add_trade_record(self, time, action='buy', price=0):
        trade = [[time, action, price]]
        trade_df = pd.DataFrame(trade, columns=['time', 'action (buy/sell)', 'price'])
        # self.trade_record = self.trade_record.append(trade_df)
        # myfile = open('trade_records.txt', "a")
        # myfile.write(str(trade) + '\n')
        base_url = f"https://api.telegram.org/bot1963957459:AAE4WESuDYvMHMUbzHnX45q1YRoUiIXFEgI/sendMessage?chat_id=-557976009&text='{trade_df}'"
        requests.get(base_url)

    def print_current_status(self):
        # current_price = self.df['close'].iloc[-1]
        current_sma1 = self.df[f'sma{self.sma1}'].iloc[-1]
        current_sma2 = self.df[f'sma{self.sma2}'].iloc[-1]
        # print(f'The current price of {self.name} is {str(current_price)}')
        print('Trading Status: ', end="")
        if self.bought is True:
            print(f'Owning {self.product_name1}')
        else:
            print(f'Owning {self.product_name2}')
        print(f'The current sma{self.sma1} is {current_sma1}')
        print(f'The current sma{self.sma2} is {current_sma2}')

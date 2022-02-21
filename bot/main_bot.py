import time, config, requests
from binance.enums import *
from datetime import datetime
from product import product
from binance.client import Client

ethbtc = product('eth', 'btc', KLINE_INTERVAL_1HOUR, sma1=5, sma2=200)    # using sma5 and sma200
# ethbtc = product('eth', 'btc', KLINE_INTERVAL_1MINUTE, sma1=5, sma2=200)    # using sma5 and sma200
ethbtc.print_url()

# cryptos = [btcusdt, ethusdt, bnbusdt]
cryptos = [ethbtc]

client = Client(config.Real_key, config.Real_secret)
tg_base_url = "https://api.telegram.org/bot1963957459:AAE4WESuDYvMHMUbzHnX45q1YRoUiIXFEgI/sendMessage?chat_id=-1001388892189&text="


def order(side, quantity, symbol, price):
    try:
        print('Sending Order')
        send_message_url = tg_base_url + f'Sending Order\nside={side}, symbol={symbol}, quantity={quantity}, price={price}.'
        requests.get(send_message_url)
        order = client.create_order(price=price, symbol=symbol, side=side, quantity=quantity, type=ORDER_TYPE_LIMIT, timeInForce="IOC")
        print(order)
    except Exception as e:
        print(f'The trade cannot be executed as an exception occurred: {e}')
        send_message_url = tg_base_url + f'The trade cannot be executed as an exception occurred: {e}'
        requests.get(send_message_url)
        return False
    return True


while True:
    print('*' * 40)
    print(f'Updated at {str(datetime.now())}')
    for coin in cryptos:
        coin.import_ticket_data()
        coin.create_smas()
        if len(coin.df['close']) >= coin.sma2:
            coin.create_buy_sell_zone()
            current_price = coin.df['close'].iloc[-1]
            current_price = str(round(current_price, 5))
            print(f'The current price of {coin.name} is {current_price}')
            coin.print_current_status()

            # Get the quantity of both the products
            my_assets = [coin.product_name1, coin.product_name2]
            for asset in my_assets:
                balance = client.get_asset_balance(asset=asset)
                print(f"I am holding {balance['free']} {balance['asset']}")

            if coin.bought_status() is False and coin.decide_to_buy():
                # Execute buy order
                print(f'Now Buy at {str(current_price)}')
                # if I am trading BTCUSDT, then I should BUY with all USDT
                product2_quantity_owned = client.get_asset_balance(asset=coin.product_name2)['free']
                if order(side=SIDE_BUY, symbol=coin.name, quantity=product2_quantity_owned, price=current_price) is True:
                    coin.add_trade_record(time=str(datetime.now()), action='buy', price=current_price)
                    print(coin.trade_record)
                    coin.bought = True

            elif coin.bought_status() is True and coin.decide_to_sell():
                # Execute sell order
                print(f'Now Sell at {str(current_price)}')
                # if I am trading BTCUSDT, then I should SELL with all BTC
                product1_quantity_owned = client.get_asset_balance(asset=coin.product_name1)['free']
                if order(side=SIDE_SELL, symbol=coin.name, quantity=product1_quantity_owned, price=current_price) is False:
                    coin.add_trade_record(time=str(datetime.now()), action='sell', price=current_price)
                    coin.trade_count += 1
                    print(coin.trade_record)
                    coin.bought = False
            else:
                # Do nothing
                # print('Do nothing')
                pass
        # coin.print_df()
        # print(coin.trade_record)
        if len(coin.df) > 200:
            coin.pop_first_data()
        # print(coin.df)
    time.sleep(5)

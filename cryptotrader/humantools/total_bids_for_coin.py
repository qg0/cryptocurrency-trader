import requests
from decimal import Decimal, localcontext
from cryptotrader.tradesignals.indicators.coinmarketcap_price import get_coinmarketcap_price
from cryptotrader.bittrex.bittrex_operator import minor_currency
import matplotlib.pyplot as plt
import csv
from time import time

class Exchange:
    GDAX = 10
    BINANCE = 20
    BITTREX = 30
    KUCOIN = 40
    CRYPTOPIA = 50
    BITFINEX = 60
    BITZ = 70
    YOBIT = 80
    HITBTC = 90
    
class Orderbook(object):
    
    def __init__(self, bids, asks):
        self._bids = bids
        self._asks = asks
        
    @property
    def bids(self):
        if self._bids == None:
            print "bids == None"
        return self._bids
    
    @property
    def asks(self):
        if self._asks == None:
            print "_asks == None"
        return self._asks

def create_ticker_for(exchange, major_currency, minor_currency):
    if exchange == Exchange.GDAX or exchange == Exchange.KUCOIN:
        return major_currency + "-" + minor_currency
    elif exchange == Exchange.BITTREX:
        return minor_currency + "-" + major_currency 
    elif exchange == Exchange.BINANCE or exchange == Exchange.BITFINEX \
    or exchange == Exchange.HITBTC:
        return major_currency + minor_currency
    elif exchange == Exchange.CRYPTOPIA or exchange == Exchange.BITZ \
    or exchange == Exchange.YOBIT:
        return major_currency + "_" + minor_currency
    else:
        raise Warning("Exchange ("+str(exchange)+")is not recognized.")

def get_gdax_orderbook(major_currency, minor_currency):
    '''
    :returns: Orderbook object. Its bids and asks will be a 2D array.
              The first dimension is each bid/ask at each price. The second dimension
              only has 3 elements each: price, size, num-orders
    '''
    ticker = create_ticker_for(Exchange.GDAX, major_currency, minor_currency)
    level = {"level":3} # Get the whole order book. Level 2 is top 50 bids/asks. Level 1 is only the best.
    orderbook = requests.get("https://api.gdax.com/products/"+ticker+"/book", params=level).json()
    return Orderbook(orderbook["bids"], orderbook["asks"])

def get_kucoin_orderbook(major_currency, minor_currency):
    '''
    :returns: Orderbook object. Its bids and asks will be a 2D array.
              The first dimension is each bid/ask at each price. The second dimension
              only has 3 elements each: price, amount, and major currency volume
    '''
    ticker = {"symbol": create_ticker_for(Exchange.KUCOIN, major_currency, minor_currency)}
    orderbook = requests.get("https://api.kucoin.com/v1/open/orders", params=ticker).json()
    return Orderbook(orderbook["data"]["BUY"], orderbook["data"]["SELL"])

def get_bittrex_orderbook(major_currency, minor_currency):
    '''
    :returns: Orderbook object. Its bids and asks will be an array.
              Each entry is a bid/ask (dictionary) with the keys: Quantity and Rate.
    '''
    ticker = create_ticker_for(Exchange.BITTREX, major_currency, minor_currency)
    params = {"type":"both", "market":ticker}
    orderbook = requests.get("https://bittrex.com/api/v1.1/public/getorderbook", params=params).json()
    return Orderbook(orderbook["result"]["buy"], orderbook["result"]["sell"])

def get_binance_orderbook(major_currency, minor_currency):
    '''
    :returns: Orderbook object. Its bids and asks will be a 2D array.
              The first dimension is each bid/ask. The second dimension
              only has 3 elements each: price, size, and a blank array that is meant to be ignored.
    '''
    ticker = create_ticker_for(Exchange.BINANCE, major_currency, minor_currency)
    params = {"symbol":ticker, "limit":1000}
    orderbook = requests.get("https://api.binance.com/api/v1/depth", params=params).json()
    return Orderbook(orderbook["bids"], orderbook["asks"])

def get_cryptopia_orderbook(major_currency, minor_currency):
    '''
    :returns: Orderbook object. Its bids and asks will be an array of dictionaries
              with the entries: "TradePairId", "Label", "Price", "Volume", and "Total"
    '''
    ticker = create_ticker_for(Exchange.CRYPTOPIA, major_currency, minor_currency)
    orderbook = requests.get("https://www.cryptopia.co.nz/api/GetMarketOrders/"+ticker).json()
    return Orderbook(orderbook["Data"]["Buy"], orderbook["Data"]["Sell"])

def get_bitfinex_orderbook(major_currency, minor_currency):
    '''
    :returns: Orderbook object. Its bids and asks will be an array of dictionaries with
              the entries: "price", "amount", and "timestamp"
    '''
    ticker = create_ticker_for(Exchange.BITFINEX, major_currency, minor_currency)
    orderbook = requests.get("https://api.bitfinex.com/v1/book/"+ticker).json()
    return Orderbook(orderbook["bids"], orderbook["asks"])

def get_bitz_orderbook(major_currency, minor_currency):
    '''
    :returns: Orderbook object. Its bids and asks will be a 2D array.
              The first dimension is each bid/ask. The second dimension
              only has 2 elements each: price, and volume.
    '''
    ticker = create_ticker_for(Exchange.BITZ, major_currency, minor_currency)
    params = {"coin":ticker}
    orderbook = requests.get("https://www.bit-z.com/api_v1/depth", params=params).json()
    return Orderbook(orderbook["data"]["bids"], orderbook["data"]["asks"])

def get_yobit_orderbook(major_currency, minor_currency):
    '''
    :returns: Orderbook object. Its bids and asks will be a 2D array.
              The first dimension is each bid/ask. The second dimension
              only has 2 elements each: price, and volume.
    '''
    ticker = create_ticker_for(Exchange.YOBIT, major_currency, minor_currency).lower()
    orderbook = requests.get("https://yobit.net/api/3/depth/"+ticker).json()
    return Orderbook(orderbook[ticker]["bids"], orderbook[ticker]["asks"])

def get_hitbtc_orderbook(major_currency, minor_currency):
    '''
    :returns: Orderbook object. Its bids and asks will be an array of dictionaries
              with the entries: "price", and "size".
    '''
    ticker = create_ticker_for(Exchange.HITBTC, major_currency, minor_currency).upper()
    params = {"limit": 0}
    orderbook = requests.get("https://api.hitbtc.com/api/2/public/orderbook/"+ticker, params=params).json()
    return Orderbook(orderbook["bid"], orderbook["ask"])

def get_sum_of_bids_and_asks(lowest_price=Decimal(0), highest_price=Decimal(10000000), major_currency="ETH", minor_currency="BTC"):
    with localcontext() as context:
        context.prec = 10
    
        # Collect the bids at the start for an accurate snapshot.
        # Requesting them, processing, then going to the next exchange
        # would mean different exchanges are queried at increasingly
        # different times.
        try:
            gdax_orderbook = get_gdax_orderbook(major_currency, minor_currency)
        except KeyError:
            print(major_currency+"/"+minor_currency+" is not listed on GDAX.")
        try:   
            bittrex_orderbook = get_bittrex_orderbook(major_currency, minor_currency)
        except (KeyError, TypeError):
            print(major_currency+"/"+minor_currency+" is not listed on Bittrex.")
        try:
            binance_orderbook = get_binance_orderbook(major_currency, minor_currency)
        except KeyError:
            print(major_currency+"/"+minor_currency+" is not listed on Binance.")
        try:
            kucoin_orderbook = get_kucoin_orderbook(major_currency, minor_currency)
        except KeyError:
            print(major_currency+"/"+minor_currency+" is not listed on Kucoin.")
        try:
            cryptopia_orderbook = get_cryptopia_orderbook(major_currency, minor_currency)
        except (KeyError, TypeError):
            print(major_currency+"/"+minor_currency+" is not listed on Cryptopia.")
        try:
            bitfinex_orderbook = get_bitfinex_orderbook(major_currency, minor_currency)
        except KeyError:
            print(major_currency+"/"+minor_currency+" is not listed on Bitfinex.")
        try:
            bitz_orderbook = get_bitz_orderbook(major_currency, minor_currency)
        except (KeyError, TypeError):
            print(major_currency+"/"+minor_currency+" is not listed on Bit-Z.")
        try:
            yobit_orderbook = get_yobit_orderbook(major_currency, minor_currency)
        except KeyError:
            print(major_currency+"/"+minor_currency+" is not listed on YoBit.")
        try:
            hitbtc_orderbook = get_hitbtc_orderbook(major_currency, minor_currency)
        except KeyError:
            print(major_currency+"/"+minor_currency+" is not listed on HitBTC.")
        
        # Get the total minor currency placed in the bids portion of the orderbook.
        bids_sum = Decimal(0) # Measured in the minor currency
        try:
            for bid in gdax_orderbook.bids:
                price = Decimal(bid[0])
                if price >= lowest_price:
                    bids_sum += price * Decimal(bid[1])
        except UnboundLocalError:
            pass # Coin is not listed on an exchange so orderbook doesn't exist.
        try:
            for bid in bittrex_orderbook.bids:
                price = Decimal(bid["Rate"])
                if price >= lowest_price:
                    bids_sum += Decimal(bid["Quantity"]) * price
        except UnboundLocalError:
            pass # Coin is not listed on an exchange so orderbook doesn't exist.
        try:
            for bid in binance_orderbook.bids:
                price = Decimal(bid[0])
                if price >= lowest_price:
                    bids_sum += Decimal(bid[1]) * price
        except UnboundLocalError:
            pass # Coin is not listed on an exchange so orderbook doesn't exist.
        try:
            for bid in kucoin_orderbook.bids:
                price = Decimal(bid[0])
                if price >= lowest_price:
                    bids_sum += Decimal(bid[2])
        except UnboundLocalError:
            pass # Coin is not listed on an exchange so orderbook doesn't exist.
        try:
            for bid in cryptopia_orderbook.bids:
                price = Decimal(bid["Price"])
                if price >= lowest_price:
                    bids_sum += Decimal(bid["Total"]) # == to Volume * Price
        except UnboundLocalError:
            pass # Coin is not listed on an exchange so orderbook doesn't exist.
        try:
            for bid in bitfinex_orderbook.bids:
                price = Decimal(bid["price"])
                if price >= lowest_price:
                    bids_sum += Decimal(bid["amount"]) * price
        except UnboundLocalError:
            pass # Coin is not listed on an exchange so orderbook doesn't exist.
        try:
            for bid in bitz_orderbook.bids:
                price = Decimal(bid[0])
                if price >= lowest_price:
                    bids_sum += Decimal(bid[1]) * price
        except UnboundLocalError:
            pass # Coin is not listed on an exchange so orderbook doesn't exist.
        try:
            for bid in yobit_orderbook.bids:
                price = Decimal(bid[0])
                if price >= lowest_price:
                    bids_sum += Decimal(bid[1]) * price
        except UnboundLocalError:
            pass # Coin is not listed on an exchange so orderbook doesn't exist.
        try:
            for bid in hitbtc_orderbook.bids:
                price = Decimal(bid["price"])
                if price >= lowest_price:
                    bids_sum += Decimal(bid["size"]) * price
        except UnboundLocalError:
            pass # Coin is not listed on an exchange so orderbook doesn't exist.
        
        # Get the total minor currency placed in the asks portion of the orderbook.
        asks_sum = Decimal(0) # Measured in the minor currency
        try:
            for bid in gdax_orderbook.asks:
                price = Decimal(bid[0])
                if price <= highest_price:
                    asks_sum += price * Decimal(bid[1])
        except UnboundLocalError:
            pass # Coin is not listed on an exchange so orderbook doesn't exist.
        try:
            for bid in bittrex_orderbook.asks:
                price = Decimal(bid["Rate"])
                if price <= highest_price:
                    asks_sum += Decimal(bid["Quantity"]) * price
        except UnboundLocalError:
            pass # Coin is not listed on an exchange so orderbook doesn't exist.
        try:
            for bid in binance_orderbook.asks:
                price = Decimal(bid[0])
                if price <= highest_price:
                    asks_sum += Decimal(bid[1]) * price
        except UnboundLocalError:
            pass # Coin is not listed on an exchange so orderbook doesn't exist.
        try:
            for bid in kucoin_orderbook.asks:
                price = Decimal(bid[0])
                if price <= highest_price:
                    asks_sum += Decimal(bid[2])
        except UnboundLocalError:
            pass # Coin is not listed on an exchange so orderbook doesn't exist.
        try:
            for bid in cryptopia_orderbook.asks:
                price = Decimal(bid["Price"])
                if price <= highest_price:
                    asks_sum += Decimal(bid["Total"]) # == to Volume * Price
        except UnboundLocalError:
            pass # Coin is not listed on an exchange so orderbook doesn't exist.
        try:
            for bid in bitfinex_orderbook.asks:
                price = Decimal(bid["price"])
                if price <= highest_price:
                    asks_sum += Decimal(bid["amount"]) * price
        except UnboundLocalError:
            pass # Coin is not listed on an exchange so orderbook doesn't exist.
        try:
            for bid in bitz_orderbook.asks:
                price = Decimal(bid[0])
                if price <= highest_price:
                    asks_sum += Decimal(bid[1]) * price
        except UnboundLocalError:
            pass # Coin is not listed on an exchange so orderbook doesn't exist.
        try:
            for bid in yobit_orderbook.asks:
                price = Decimal(bid[0])
                if price <= highest_price:
                    asks_sum += Decimal(bid[1]) * price
        except UnboundLocalError:
            pass # Coin is not listed on an exchange so orderbook doesn't exist.
        try:
            for bid in hitbtc_orderbook.asks:
                price = Decimal(bid["price"])
                if price <= highest_price:
                    asks_sum += Decimal(bid["size"]) * price
        except UnboundLocalError:
            pass # Coin is not listed on an exchange so orderbook doesn't exist.
    
    return (bids_sum, asks_sum)

def append_to_historical_orderbook_data(coin_name, bids_sum, asks_sum,price):
    with open(coin_name+'_orderbook_sum_history.csv', 'a') as history_file:
        writer = csv.writer(history_file)
        writer.writerow([bids_sum,asks_sum,price,time()])

def plot_orderbook_over_time(coin_name):
    with open(coin_name+'_orderbook_sum_history.csv', 'r') as history_file:
        reader = csv.reader(history_file)
        sum_of_bids = []
        sum_of_asks = []
        time_stamps = []
        for row in reader:
            sum_of_bids.append(row[0])
            sum_of_asks.append(row[1])
            # row[2] is the historical price and is not used
            # It is in the csv file to test the correlation between the orderbook
            # and price movements.
            time_stamps.append(row[3])
        plt.plot(time_stamps, sum_of_bids, label="Sum of Bids")
        plt.plot(time_stamps, sum_of_asks, label="Sum of Asks")
        plt.legend()
        plt.xlabel("Time (ms)")
        plt.ylabel("Sum of orderbook (BTC)")
        plt.show()
        
def update_historical_ethereum_data():
    ''' Sums the top 20% of bids and bottom 20% of asks then plots them against historical sums. '''
    coinmarketcap_id = "ethereum"
    price = get_coinmarketcap_price(coinmarketcap_id)
    lower_bound = price * Decimal(0.8) # Top 20% of bids
    upper_bound = price * Decimal(1.2) # Bottom 20% of asks
    bids_sum, asks_sum = get_sum_of_bids_and_asks(lowest_price=lower_bound, highest_price=upper_bound, major_currency="ETH")
    append_to_historical_orderbook_data(coinmarketcap_id, bids_sum, asks_sum, price)
    plot_orderbook_over_time(coinmarketcap_id)

def fetch_orderbook_data_once():
    print("Please enter the name of the coin you want info for. It should be lowercase and spaces should be replaced with -")
    coinmarketcap_id = raw_input("")
    price = get_coinmarketcap_price(coinmarketcap_id)
    print("This script will sum the top X% of bids in the orderbook. What should X be?")
    print("For example, the top third of bids would be 33.")
    top = Decimal(raw_input(""))
    lower_bound = price * (Decimal(1) - top) # Top % of bids
    upper_bound = price * (Decimal(1) + top) # Bottom % of asks
    print("Please enter the ticker for the coin you want info for.")
    major_currency = raw_input("").upper()
    
    bids_sum, asks_sum = get_sum_of_bids_and_asks(lowest_price=lower_bound, highest_price=upper_bound, major_currency=major_currency)
    print "Sum of top "+str(top)+"% of bids: " + str(bids_sum) + " " + minor_currency
    print "Sum of bottom "+str(top)+"% of asks: " + str(asks_sum) + " " + minor_currency

if __name__ == "__main__":
    #fetch_orderbook_data_once()
    update_historical_ethereum_data()
    
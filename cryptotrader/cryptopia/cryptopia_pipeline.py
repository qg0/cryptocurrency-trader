'''
Loads data from Cryptopia.

@author: Tobias Carryer
'''

import time
from threading import Thread
import requests

class CryptopiaPipeline(object):
    def __init__(self, on_order_book, market_ticker="BTC_USDT", poll_time=15):
        '''
        on_order_book should have 2 parameters: one for the bids and one for the asks.
        on_order_book will be called every [poll_time] seconds
        
        Pre: market_ticker is a String in Cryptopia's format
             poll_time is a positive integer
        '''
        
        self.on_order_book = on_order_book
        self.order_book_url = "https://www.cryptopia.co.nz/api/GetMarketOrders/" + market_ticker
        self.poll_time = poll_time
        self._time_started = 0
        
        self.stop = False
        self.thread = None

    def start(self):
        def _go():
            last_time = 0
            while True:
                if self.stop:
                    print "Stopping Cryptopia pipeline."
                    break
                elif time.time() - last_time >= self.poll_time:
                    last_time = time.time()
                    order_book = self.get_order_book()
                    self.on_order_book(order_book["Buy"], order_book["Sell"])

        self.thread = Thread(target=_go)
        self.stop = False
        self.thread.start()
        print("Started Cryptopia pipeline.")

    def get_order_book(self):
        '''
        Pre: self.order_book_url is valid
        Returns: JSON Dictionary with two entries "Buy" and "Sell".
                 Within those entries, there is an array of dictionaries that have
                 the entries: "TradePairId", "Label", "Price", "Volume", and "Total"
        '''

        data = requests.get(self.order_book_url).json()["Data"]
        return data

    def stop(self):
        if not self.stop:
            self.stop = True

if __name__ == "__main__":
    def on_order_book(bids, asks):
        print("on_order_book was called.")
        print("Highest bid: "+str(bids[0]["Price"])+"USDT for "+str(bids[0]["Volume"])+"ETH.")
        print("Second highest bid: "+str(bids[1]["Price"])+"USDT for "+str(bids[1]["Volume"])+"ETH.")
        print("Lowest ask: "+str(asks[0]["Price"])+"USDT for "+str(asks[0]["Volume"])+"ETH.")
        print("Second lowest ask: "+str(asks[1]["Price"])+"USDT for "+str(asks[1]["Volume"])+"ETH.")
        
    pipeline = CryptopiaPipeline(on_order_book, "ETH_USDT", 15)
    pipeline.start()
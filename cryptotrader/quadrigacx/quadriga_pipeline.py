'''
Loads data from QuadrigaCX.

@author: Tobias Carryer
'''

import time
from threading import Thread
import requests
from quadriga_options import QuadrigaTickers

class QuadrigaPipeline(object):
    def __init__(self, on_order_book, market_ticker=QuadrigaTickers.BTC_CAD, poll_time=15):
        '''
        on_order_book should have 2 parameters: one for the bids and one for the asks.
        on_order_book will be called every [poll_time] seconds
        
        Pre: market_ticker is a String in Quadriga's ticker format.
             poll_time is a positive integer
        '''
        
        self.on_order_book = on_order_book
        self.order_book_url = "https://api.quadrigacx.com/v2/order_book?book=" + market_ticker
        self.poll_time = poll_time
        self._time_started = 0
        
        self.stop = False
        self.thread = None

    def start(self):
        def _go():
            last_time = 0
            while True:
                if self.stop:
                    print "Stopping QuadrigaCX pipeline."
                    break
                elif time.time() - last_time >= self.poll_time:
                    last_time = time.time()
                    order_book = self.get_order_book()
                    self.on_order_book(order_book["bids"], order_book["asks"])

        self.thread = Thread(target=_go)
        self.stop = False
        self.thread.start()
        print("Started QuadrigaCX pipeline.")

    def get_order_book(self):
        '''
        Pre: self.order_book_url is valid
        Returns: JSON Dictionary with the entries "timestamp", "bids", and "asks"
                 The bids and asks are two 2D lists. Each entry has exactly two entries
                 in its second level, index 0 is the  order's price, and
                 index 1 is the order's amount.
        '''

        data = requests.get(self.order_book_url).json()
        return data

    def stop(self):
        if not self.stop:
            self.stop = True

if __name__ == "__main__":

    def on_order_book(bids, asks):
        print("on_order_book was called.")
        print("Highest bid: "+bids[0][0]+"CAD for "+bids[0][1]+"ETH.")
        print("Lowest ask: "+asks[0][0]+"CAD for "+asks[0][1]+"ETH.")
        
    pipeline = QuadrigaPipeline(on_order_book, QuadrigaTickers.ETH_CAD, 15)
    pipeline.start()
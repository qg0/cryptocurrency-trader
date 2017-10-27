'''
Loads data from Bittrex.

@author: Tobias Carryer
'''

from cryptotrader.librariesrequired.bittrex.bittrex import Bittrex
import time
from threading import Thread
from bittrex_ignore import BittrexSecret
   
class BittrexPipeline(object):
    def __init__(self, on_market_summary, poll_time=15, minor_currency="BTC"):
        '''
        on_market_summary should have 1 parameter: the json object containing the market summary
                                                   as specified by Bittrex's API.
        
        Pre: poll_time is a positive integer
        Post: on_market_summary is called every [poll_time] seconds for every market that has
              [minor_currency] as the minor currency.
        '''
        
        self.on_market_summary = on_market_summary
        self.bittrex_api = Bittrex(BittrexSecret.api_key, BittrexSecret.api_secret)
        self.poll_time = poll_time
        self.minor_currency = minor_currency
        self._time_started = 0
        
        self.stop = False
        self.thread = None

    def start(self):
        def _go():
            last_time = 0
            while True:
                if self.stop:
                    print "Stopping Bittrex pipeline."
                    break
                elif time.time() - last_time >= self.poll_time:
                    last_time = time.time()
                    market_summaries = self.bittrex_api.get_market_summaries()
                    for market_summary in market_summaries["result"]:
                        if market_summary["MarketName"].startswith(self.minor_currency):
                            trading = market_summary["MarketName"].replace(self.minor_currency+"-", '')
                            self.on_market_summary(market_summary, trading)

        self.thread = Thread(target=_go)
        self.stop = False
        self.thread.start()
        print("Started Bittrex pipeline.")

    def stop(self):
        if not self.stop:
            self.stop = True

if __name__ == "__main__":

    def on_market_summary(market_summary, trading):
        print("on_market_summary was called for market: "+trading)
        print("Highest bid: "+str(market_summary["Bid"])+"BTC")
        print("Lowest ask: "+str(market_summary["Ask"])+"BTC")
        
    pipeline = BittrexPipeline(on_market_summary)
    pipeline.start()
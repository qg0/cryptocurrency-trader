'''
Loads data from Binance.

@author: Tobias Carryer
'''

import time
from threading import Thread
import requests
   
class BinancePipeline(object):
    def __init__(self, on_market_summary, market, poll_time=15):
        '''
        Pre: poll_time is a positive integer
             on_market_summary has 2 parameters: the highest bid and the lowest ask
        Post: on_market_summary is called every [poll_time] seconds for every market that has
              [minor_currency] as the minor currency.
        '''
        
        self.on_market_summary = on_market_summary
        self.poll_time = poll_time
        self._time_started = 0
        self.market = market
        
        self.stop = False
        self.thread = None
        
        self.get_average_latency()
        
    def start(self):
        def _go():
            last_time = 0
            while True:
                if self._stop:
                    print "Stopping Binance pipeline."
                    break
                elif time.time() - last_time >= self.poll_time:
                    last_time = time.time()
                    orderbook = self.get_orderbook(self.market)
                    bids = orderbook["bids"]
                    asks = orderbook["asks"]
                    self.on_market_summary(bids[0][0], asks[0][0])

        self.thread = Thread(target=_go)
        self._stop = False
        self.thread.start()
            
        print("Started Binance pipeline for market: " + self.market)
        
    def get_average_latency(self):
        '''
        Based on the algorithm by Zachary Booth Simpson (2000)
        http://www.mine-control.com/zack/timesync/timesync.html
        
        Latency is measured in milliseconds.
        '''
        
        print("Calculating the average latency to Binance.")
        
        client_times = []
        server_times = []
            
        # Exclude the first ping. It is abnormally long for some reason.
        requests.get("https://api.binance.com/api/v1/time")
        
        i = 0
        while i < 8: # Arbitrary, but change averages below if this is changed
            client_times.append(round(time.time()*1000)) # seconds to milliseconds
            server_times.append(requests.get("https://api.binance.com/api/v1/time").json()["serverTime"])
            i += 1
        
        # Divide by two because the latency exists when the package is being sent there AND back
        average_server_time = sum(server_times) / 8.0
        average_client_time = sum(client_times) / 8.0
        time_dif = average_server_time - average_client_time
        self.latency_between_server_and_client = int(round(time_dif / 2.0))
        
    def get_timestamp(self):
        '''
        Accounts for the difference between the client and the server time.
        '''
        client_time = int(round(time.time() * 1000))
        return client_time + self.latency_between_server_and_client
        
    def get_orderbook(self, market):
        params = [("symbol", market)]
        return requests.get("https://api.binance.com/api/v1/depth", params=params).json()

    def stop(self):
        if not self.stop:
            self.stop = True

if __name__ == "__main__":

    def on_market_summary(highest_bid, lowest_ask):
        print("Highest bid: "+str(highest_bid)+"BTC")
        print("Lowest ask: "+str(lowest_ask)+"BTC")
        
    pipeline = BinancePipeline(on_market_summary, "ETHBTC")
    pipeline.start()
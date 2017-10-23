'''
Loads data from GDAX.

@author: Tobias Carryer
'''

import json
import time
from threading import Thread
import urllib2

#Requires websocket-client from https://github.com/websocket-client/websocket-client
from cryptotrader.librariesrequired.websocket import create_connection, WebSocketConnectionClosedException

def load_historical_data():
        '''
        Pre: Historical data is in chronological order.
        '''
        
        values = []
        timestamps = []
        trades_at_time = []
        last_timestamp = 0
        
        with open("coinbaseUSD.csv") as f:
            for line in f:
                
                contents = line.split(",")
                timestamp = float(contents[0]) #UNIX Timestamp
                value = float(contents[1])
                    
                #Average value of all trades that happened at the same moment
                #Assumes timestamps are in chronological order
                if timestamp == last_timestamp:
                    index = len(values)-1
                    values[index] = ((values[index] * values[index]) + value) / (trades_at_time[index] + 1)
                    trades_at_time[index] += 1
                elif timestamp > last_timestamp:
                    values.append(value)
                    trades_at_time.append(1)
                    timestamps.append(timestamp)
                else:
                    print("ERROR: Unexpected timestamp "+str(timestamp)+" after "+str(last_timestamp)+". Violates assertion that timestamps / entries in the historical data are in chronological order.")
                
                last_timestamp = timestamp
                
        print("Finished loading historical data.")
        
        return [values, timestamps]
    
class GDAXPipeline(object):
    def __init__(self, on_market_value, product, minutes_to_reset=15):
        '''
        on_data_point is called every time a new data point is received from the websocket.
        on_data_point should have 2 parameters, websocket, and message.
        message["price"] can be used to get the currency price of product.
        
        minutes_to_reset is used to force a disconnect and reconnect to the websocket
        every so many minutes
        
        Pre: product is not a list
             minutes_to_reset is positive
        '''
        
        self.on_market_value = on_market_value
        self.url = "wss://ws-feed.gdax.com"
        self.product = product.lower()
        self.seconds_to_reset = minutes_to_reset * 60 #Time in seconds
        self._time_started = 0
        
        self.stop = False
        self.ws = None
        self.thread = None

    def start(self):
        def _go():
            self._connect()
            self._listen()

        self.thread = Thread(target=_go)
        self.thread.start()
        print("Started GDAX pipeline. Uses GDAX's websocket API.")

    def _connect(self):
        '''
        Post: self.ws is not None
              self.stop == False
        '''
        
        if not isinstance(self.product, list):
            self.product = [self.product]
        sub_params = {'type': 'subscribe', 'product_ids': self.product}

        self.ws = create_connection(self.url)
        self.ws.send(json.dumps(sub_params))
        self.ws.send(json.dumps({"type": "heartbeat", "on": True}))
        self._time_started = int(time.time())
        self.stop = False
        
    def _listen(self):
        while not self.stop:
            #Force websocket reset every given amount of time
            if int(time.time()) - self._time_started >= self.seconds_to_reset:
                print("GDAXPipeline: Forcing websocket reconnect.")
                self.close()
                self._connect()
            else:
                try:
                    if int(time.time() % 30) == 0:
                        # Set a 30 second ping to keep connection alive
                        self.ws.ping("keepalive")
                    msg = json.loads(self.ws.recv())
                except Exception as e:
                    print(e)
                else:
                    
                    if msg["type"] == "heartbeat":
                        #Get the ticker price
                        ticker = urllib2.urlopen("https://api.gdax.com/products/"+self.product[0]+"/ticker").read()
                        market_value = json.loads(ticker)["price"]
                        
                        #The same value is likely to be sent multiple times so there are
                        #60 data points per minute
                        self.on_market_value(float(market_value))
                    elif msg["type"] == "error":
                        print(msg["message"])
                        print("CLOSING WEBSOCKET")
                        self.close()

    def close(self):
        if not self.stop:
            self.stop = True
            try:
                if self.ws:
                    self.ws.send(json.dumps({"type": "heartbeat", "on": False}))
                    self.ws.close()
            except WebSocketConnectionClosedException as e:
                print("WebSocketConnectionClosedException: " + e)

if __name__ == "__main__":
    def on_market_value(value):
        print("on_market_value was called with value: "+str(value))
        
    pipeline = GDAXPipeline(on_market_value, "ETH-BTC")
    pipeline.start()
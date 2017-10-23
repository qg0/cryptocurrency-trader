'''
Loads data from Bitfinex.

@author: Tobias Carryer
'''

import json
import time
from threading import Thread
import urllib2
import ast

#Requires websocket-client from https://github.com/websocket-client/websocket-client
from cryptotrader.librariesrequired.websocket import create_connection, WebSocketConnectionClosedException
    
class BitfinexPipeline(object):
    def __init__(self, on_market_value, product, use_ask_value=False, minutes_to_reset=15):
        '''
        on_market_value is called every time a new data point is received from the websocket.
        on_market_value should have 2 parameters, websocket, and message.
        message["last_price"] can be used to get the currency price of product.
        
        minutes_to_reset is used to force a disconnect and reconnect to the websocket
        every so many minutes
        
        Pre: product is not a list
             minutes_to_reset is positive
        '''
        
        self.on_market_value = on_market_value
        self.url = "wss://api.bitfinex.com/ws"
        self.product = product.lower()
        self.use_ask_value = use_ask_value
        self.seconds_to_reset = minutes_to_reset * 60 #Time in seconds
        self._time_started = 0
        
        #GET Request the API to get the current value
        #Value is only set when it changes so multiple seconds could pass without
        #calling on_market_value if this is not done
        ticker = urllib2.urlopen("https://api.bitfinex.com/v1/pubticker/"+str(product)).read()
        self.last_market_value = float(json.loads(ticker)["last_price"])
        
        self.stop = False
        self.ws = None
        self.thread = None

    def start(self):
        def _go():
            self._connect()
            self._listen()

        self.thread = Thread(target=_go)
        self.thread.start()
        print("Started Bitfinex pipeline. Uses Bitfinex's websocket API.")

    def _connect(self):
        '''
        Post: self.ws is not None
              self.stop == False
        '''
        
        sub_params = {'event': 'subscribe', 'channel':'ticker', 'pair': self.product}

        self.ws = create_connection(self.url)
        self.ws.send(json.dumps(sub_params))
        self._time_started = int(time.time())
        self.stop = False
        
    def _listen(self):
        while not self.stop:
            #Force websocket reset every given amount of time
            if int(time.time()) - self._time_started >= self.seconds_to_reset:
                print("BitfinexPipeline: Forcing websocket reconnect.")
                self.close()
                self._connect()
            else:
                try:
                    if int(time.time() % 30) == 0:
                        # Set a 30 second ping to keep connection alive
                        self.ws.ping("keepalive")
                    
                    msg = ast.literal_eval(self.ws.recv())
                    
                    if len(msg) == 11:
                        #Index 3 is ask price, Index 7 is last price
                        if self.use_ask_value:
                            self.last_market_value = float(msg[3])
                        else:
                            self.last_market_value = float(msg[7])
                    self.on_market_value(self.last_market_value)
                except Exception as e:
                    print("Exception: "+str(e))

    def close(self):
        if not self.stop:
            self.stop = True
            try:
                if self.ws:
                    self.ws.close()
            except WebSocketConnectionClosedException as e:
                print("WebSocketConnectionClosedException: " + e)

if __name__ == "__main__":
    def on_market_value(value):
        print("on_market_value was called with value: "+str(value))
        
    pipeline = BitfinexPipeline(on_market_value, "ETHBTC", True)
    pipeline.start()
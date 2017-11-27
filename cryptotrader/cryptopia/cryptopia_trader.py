'''
Implements the Cryptopia API for live and simulation trading.
Note: Cryptopia's API does not have a way to check if an order was filled. Other bots
      abort when an order is cancelled, this one just fetches the balance again and
      keeps going. To allow a human to remotely disable the bot, a sell order for
      0.00000001 NEO will be placed for 5500BTC. If that sell order is cancelled,
      the bot will shut down. For this reason, Cryptopia must always have 0.00000001 NEO
      available before running an instance of the bot.
@author: Tobias Carryer
'''

import hmac
import hashlib
import base64
import time
import requests
import sys
import urllib
import json
from decimal import Decimal, localcontext
from cryptotrader import Trader, DefaultPosition
from cryptopia_options import minimum_trade_for
from cryptotrader.cryptopia.cryptopia_options import cryptopia_fee

class CryptopiaTrader(Trader):
        
    simulation_buy_order_id = "1234"
    simulation_sell_order_id = "4321"
    emergency_shutdown_location = "NEO_BTC"
        
    def __init__(self, trading_pair, percentage_to_trade=1, start_by_buying=True, starting_amount=1):
        '''
        Post: self.is_test = True until authenticate() is called
        '''
        
        # Split up the trading pair for currency specific options and for console output.
        self.product = trading_pair
        split_pair = trading_pair.split("_")
        self.major_currency = split_pair[0]
        self.minor_currency = split_pair[1]
        
        # Trader is in test mode by default.
        # minimum_trade is the minimum amount of assets that can be sold on a trade.
        Trader.__init__(self, True, minimum_trade_for[self.minor_currency])
        
        # Will be set to a number (order ID) when an order is placed.
        self._waiting_for_order_to_fill = None
        
        # In test mode: Is used to prevent the same transaction from being counted twice.
        self._last_simulation_transaction_check = 0
        
        # In test mode: tracks how much the trader's order has been filled.
        self._expecting_simulation_balance = 0
        self._expecting_simulation_assets = 0
        self._filled_simulation_balance = 0
        self._filled_simulation_assets = 0
        
        # Used when aborting to determine if any positions need to be closed.
        self._active_buy_order = False
        self._active_sell_order = False
        
        self.percentage_to_trade = Decimal(percentage_to_trade)
        self.amount_precision = 8
        self.price_precision = 8
        self.start_by_buying = start_by_buying
        
        with localcontext() as context:
            context.prec = 8
            
            if self.start_by_buying:
                self.balance = Decimal(starting_amount)
                self.assets = Decimal(0)
            else:
                self.balance = Decimal(0)
                self.assets = Decimal(starting_amount)
            self.post_fee = Decimal(1) - cryptopia_fee
            
    def authenticate(self, api_key, api_secret):
        self.is_test = False
        self.api_key = api_key
        self.api_secret = api_secret
        self.set_up_emergency_shutdown()
        self.fetch_balance_and_assets()
        if self.start_by_buying:
            self.assets = Decimal(0)
        else:
            self.balance = Decimal(0)
        
    def should_default_to(self, default_position, aggressive=False):
        '''
        True == hold/buy major currency when the market is unprofitable
        False == hold/sell to get minor currency when market is unprofitable 
        None == hold whatever the trader has
        
        aggressive == True: sell/buy at a loss when told to hold to guarantee the default position is held.
        '''
        self.default_position = default_position
        self.aggressive = aggressive
        
    def fetch_balance_and_assets(self):
        '''
        Get the balance and assets this trader has permission to spend in the exchange.
        Pre: API Key, client, and API secret have been set.
        Post: self.balance and self.assets are set. They are a percentage of the actual balance/assets
              if percentage_to_trade is set in the constructor.
        '''
        
        if self.is_test:
            print("Warning: fetch_balance was called when trader is in test mode.")
        else:
            
            url = "https://www.cryptopia.co.nz/api/GetBalance"
            
            #Fetch available minor currency from the exchange
            post_data_minor = json.dumps({"Currency": self.minor_currency})
            header_minor = self.create_authenticated_header(url, post_data_minor)
            r_minor = requests.post(url, data=post_data_minor, headers=header_minor)
            data_minor = r_minor.json()["Data"]
            self.balance = Decimal(data_minor[0]["Available"]) * self.percentage_to_trade
            
            #Fetch available major currency from the exchange
            post_data_major = json.dumps({"Currency": self.major_currency})
            header_major = self.create_authenticated_header(url, post_data_major)
            r_major = requests.post(url, data=post_data_major, headers=header_major)
            data_major = r_major.json()["Data"]
            self.assets = Decimal(data_major[0]["Available"]) * self.percentage_to_trade
            
            print("Trading with: "+str(round(self.balance, 3))+self.minor_currency+" and "+str(round(self.assets,3))+self.major_currency)
        
    def buy(self, market_value):
        self.check_for_abort()
        
        if self._waiting_for_order_to_fill != None:
            self.was_order_filled(self._waiting_for_order_to_fill)
        
        if self.can_buy == True:
                
            # Prevent selling while a buy order is active.
            if self._waiting_for_order_to_fill == None:    
            
                #Always spend all the balance. A percentage of it was allocated to the trader at the start.
                assets_to_buy = self.balance / market_value
                if assets_to_buy >= self.minimum_trade:
                    
                    self._active_buy_order = True
                    
                    if self.is_test:
                        self.simulation_buy(assets_to_buy)
                    else:
                        self.limit_buy_order(market_value)
                    
                    print("Buying. Planning to spend: "+str(self.balance)+self.minor_currency)
                    self.balance = Decimal(0)
                else:
                    sys.stdout.write('b ')
                    
            else:
                sys.stdout.write('wb ')
              
    def limit_buy_order(self, market_value):
        url = "https://www.cryptopia.co.nz/api/SubmitTrade"
        post_data = json.dumps({"Market": self.product,
                     "Amount": round(float(self.balance / market_value), self.amount_precision),
                     "Rate": round(market_value, self.price_precision),
                     "Type": "Buy"})
        header = self.create_authenticated_header(url, post_data)
        r = requests.post(url, data=post_data, headers=header)
        self._waiting_for_order_to_fill = r.json()["Data"]["OrderId"]
        self._active_buy_order = True
                
    def simulation_buy(self, assets_to_buy):
        self._waiting_for_order_to_fill = CryptopiaTrader.simulation_buy_order_id
                    
        # Order will not be "filled" until
        # filled_simulation_assets == expecting_simulation_assets
        self._expecting_simulation_assets = assets_to_buy
        self._filled_simulation_assets = 0
        
        # Only orders that matter are the ones that might fill us which can only
        # happen in the future.
        self._last_simulation_transaction_check = time.time()
        
        self._active_buy_order = True
        
    def sell(self, market_value):
        self.check_for_abort()
        
        if self._waiting_for_order_to_fill != None:
            self.was_order_filled(self._waiting_for_order_to_fill)
            
        if self.can_sell:
            
            # Prevent selling while a buy order is active.
            if self._waiting_for_order_to_fill == None:
            
                #Always sell all assets. A percentage of them was allocated to the trader at the start.
                if self.assets >= self.minimum_trade:
                    
                    self._active_sell_order = True
                    
                    if self.is_test:
                        self.simulation_sell(market_value)
                    else:
                        self.limit_sell_order(market_value)
                    
                    print("Selling. Planning to get balance: "+str(self.assets * market_value * self.post_fee)+self.minor_currency)
                    self.assets = Decimal(0)
                else:
                    sys.stdout.write('s ')
                    
            else:
                sys.stdout.write('ws ')
                
    def limit_sell_order(self, market_value):
        url = "https://www.cryptopia.co.nz/api/SubmitTrade"
        post_data = json.dumps({"Market": self.product,
                                "Amount": round(float(self.assets), self.amount_precision),
                                "Rate": round(market_value, self.price_precision),
                                "Type": "Sell"})
        header = self.create_authenticated_header(url, post_data)
        
        r = requests.post(url, data=post_data, headers=header)
        self._waiting_for_order_to_fill = r.json()["Data"]["OrderId"]
        self._active_sell_order = True
                
    def simulation_sell(self, market_value):
        self._waiting_for_order_to_fill = CryptopiaTrader.simulation_sell_order_id
                    
        # Order will not be "filled" until
        # _filled_simulation_balance == _expecting_simulation_balance
        self._expecting_simulation_balance = self.assets * market_value
        self._filled_simulation_balance = 0
        
        # Used to track how much balance is earned from partial fills.
        self._limit_order_price = market_value
        
        # Only orders that matter are the ones that might fill us which can only
        # happen in the future.
        self._last_simulation_transaction_check = time.time()
        
        self._active_sell_order = True
            
    def was_order_filled(self, order_id):
        '''
        Post: Internal balance/assets is updated if the order was filled.
        '''
        
        if self.is_test:
            try:
                assert(order_id == CryptopiaTrader.simulation_buy_order_id or 
                       order_id == CryptopiaTrader.simulation_sell_order_id)
            except AssertionError as e:
                e.args += ("Invalid order ID: ", order_id)
                raise
            
            # Simulate the trader's order being filled by watching what the market.
            # It is likely that simulation mode results in higher profits as in reality
            # other bots undercut our own trades so our orders are filled less frequently.
            
            # The time frame is an hour because the pipeline's polling frequency
            # could be set to be longer than the default number of seconds.
            r = requests.get('https://www.cryptopia.co.nz/api/GetMarketHistory/'+self.product+"/1")
            
            for trade in r.json()["Data"]:
                if int(trade["Timestamp"]) < self._last_simulation_transaction_check:
                    break
                else:
                    with localcontext() as context:
                        context.prec = 8
                        
                        if order_id == CryptopiaTrader.simulation_buy_order_id and trade["Type"] == "Sell":
                            self._filled_simulation_assets += Decimal(trade["Amount"])
                            if self._filled_simulation_assets >= self._expecting_simulation_assets:
                                self.assets = self._expecting_simulation_assets * self.post_fee
                                self._active_buy_order = False
                                self._waiting_for_order_to_fill = None
                        elif order_id == CryptopiaTrader.simulation_sell_order_id and trade["Type"] == "Buy":
                            incoming_balance = Decimal(trade["Amount"]) * self._limit_order_price
                            self._filled_simulation_balance += incoming_balance
                            if self._filled_simulation_balance >= self._expecting_simulation_balance:
                                self.balance = self._expecting_simulation_balance * self.post_fee
                                self._active_sell_order = False
                                self._waiting_for_order_to_fill = None
                                
            # Orders up to this moment have been processed, don't process them again.
            self._last_simulation_transaction_check = time.time()
            
        else:
            
            # Lookup the order on the market and check its status.
            # The trader will stop if the order was cancelled as a human intervened.
            # Note: The pipeline never knows the Trader's status so the pipeline will continue
            #       to pass data to the market observer.
            
            open_order = self.lookup_open_order(order_id, self.product)
            
            if open_order == None:
                # Order was filled or cancelled.
                self.fetch_balance_and_assets()
                if self._active_buy_order:
                    self._active_buy_order = False
                    self.balance = Decimal(0)
                else:
                    self._active_sell_order = False
                    self.assets = Decimal(0)
                self._waiting_for_order_to_fill = None
            elif open_order["Remaining"] < open_order["Amount"]:
                print("The order has been partially filled. Waiting until it is fully filled.")
    
    def hold(self, market_value):
        ''' Cancel any open orders and revert back to the default position depending on aggressiveness. '''
        
        if self._waiting_for_order_to_fill != None:
            self.was_order_filled(self._waiting_for_order_to_fill)
        
        # Might cause a loss.
        if self.aggressive:
        
            if self.default_position == DefaultPosition.BUY:
                # Cancel sell order
                if self._active_sell_order:
                    if not self.is_test:
                        self.cancel_order(self._waiting_for_order_to_fill)
                    self._waiting_for_order_to_fill = None
                    self._active_sell_order = False
            
                # Buy with any remaining balance
                if self.is_test:
                    if self._filled_simulation_balance > 0:
                        self.simulation_buy(self._filled_simulation_balance / market_value)
                        self._active_buy_order = True
                        print("Buying at a loss.")
                elif self.balance > 0:
                    self.limit_buy_order(market_value)
                    self._active_buy_order = True
                    print("Buying at a loss.")
    
            elif self.default_position == DefaultPosition.SELL:
                # Cancel buy order
                if self._active_buy_order:
                    if not self.is_test:
                        self.cancel_order(self._waiting_for_order_to_fill)
                    self._waiting_for_order_to_fill = None
                    self._active_buy_order = False
                
                # Sell any remaining assets
                if self.is_test:
                    if self._filled_simulation_assets > 0:
                        self.simulation_sell(market_value)
                        self._active_sell_order = True
                        print("Selling at a loss.")
                elif self.assets > 0:
                    self.limit_sell_order(market_value)
                    self._active_sell_order = True
                    print("Selling at a loss.")
        else:
            # Keep orders open if they help reach the default position.
            if self._active_sell_order and self.default_position != DefaultPosition.SELL:
                if not self.is_test:
                    self.cancel_order(self._waiting_for_order_to_fill)
                self._waiting_for_order_to_fill = None
                self._active_sell_order = False
        
            if self._active_buy_order and self.default_position != DefaultPosition.BUY:
                if not self.is_test:
                    self.cancel_order(self._waiting_for_order_to_fill)
                self._waiting_for_order_to_fill = None
                self._active_buy_order = False
    
    def cancel_order(self, order_id):
        order_info = self.lookup_open_order(order_id, self.product)
        if order_info == None:
            print("cancel_order was called but the order was already filled or cancelled.")
        else:
            if order_info["Type"] == "Buy":
                self.balance = Decimal(order_info["Rate"]) * Decimal(order_info["Amount"])
            else:
                self.assets = Decimal(order_info["Amount"])
                
            url = "https://www.cryptopia.co.nz/api/CancelTrade"
            post_data = json.dumps({"Type": "Trade", "OrderId": order_id})
            header = self.create_authenticated_header(url, post_data)
            requests.post(url, data=post_data, headers=header)
    
    def abort(self):
        Trader.abort(self)
        self._waiting_for_order_to_fill = None
        print("CryptopiaTrader is shutting down.")
        
    def lookup_open_order(self, order_id, market):
        url = "https://www.cryptopia.co.nz/api/GetOpenOrders"
        post_data = json.dumps({"Market": market})
        header = self.create_authenticated_header(url, post_data)
        r = requests.post(url, data=post_data, headers=header)
        j = r.json()
        if not j["Success"]:
            raise Warning(j["Error"])
        else:
            for open_trade in j["Data"]:
                if open_trade["OrderId"] == order_id:
                    return open_trade
                
    def set_up_emergency_shutdown(self):
        url = "https://www.cryptopia.co.nz/api/SubmitTrade"
        post_data = json.dumps({"Market": self.emergency_shutdown_location,
                                "Amount": 0.00000001,
                                "Rate": 5500.00000000,
                                "Type": "Sell"})
        header = self.create_authenticated_header(url, post_data)
        r = requests.post(url, data=post_data, headers=header)
        self.emergency_shutdown_id = r.json()["Data"]["OrderId"]
        
    def check_for_abort(self):
        if self.emergency_shutdown_id != None and self.lookup_open_order(self.emergency_shutdown_id, self.emergency_shutdown_location) == None:
            print("Emergency abort order was cancelled.")
            self.abort()
    
    def create_authenticated_header(self, url, post_data):
        ''' Pre: API Key, client, and API secret have been set. '''
        nonce = str(time.time()*100)
        rcb64 = base64.b64encode(hashlib.md5(post_data).digest())
        signature = self.api_key + "POST" + urllib.quote_plus(url).lower() + nonce + rcb64
        hmacsignature = base64.b64encode(hmac.new(base64.b64decode(self.api_secret), signature, hashlib.sha256).digest())
        header_value = "amx " + self.api_key + ":" + hmacsignature + ":" + nonce
        return {'Authorization': header_value, 'Content-Type': 'application/json; charset=utf-8'}
    
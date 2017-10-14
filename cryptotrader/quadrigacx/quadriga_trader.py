'''
Implements the QuadrigaCX API for live and simulation trading.
@author: Tobias Carryer
'''

import hmac
import hashlib
import time
import requests
import sys
from decimal import Decimal, localcontext
from cryptotrader.trader import Trader

class QuadrigaTrader(Trader):
        
    simulation_buy_order_id = 1234
    simulation_sell_order_id = 4321
        
    def __init__(self, options, default_position=False, percentage_to_trade=1, fee=0.005, starting_test_balance=100):
        '''
        default_position is whether the Trader should hold the minor currency (sell, False) or
        the major currency (buy / True) after scalping the market. For example, in a USD-CAD market
        True would mean CAD is held after scalping and False would mean USD is held after scalping.
        
        default_position must be False when in test mode.
        
        Pre: options is an instance of QuadrigaOptions and must have pair and ticker set.
        Post: self.is_test = True until authenticate() is called
        '''
        
        # Trader is in test mode by default.
        # minimum_trade is the minimum amount of assets that can be sold on a trade.
        Trader.__init__(self, True, options.minimum_trade)
        
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
        
        self.default_position = default_position
        self.product = options.ticker
        self.major_currency = options.major_currency
        self.minor_currency = options.minor_currency
        self.percentage_to_trade = Decimal(percentage_to_trade)
        
        with localcontext() as context:
            context.prec = 8
            
            self.balance = Decimal(starting_test_balance)
            self.assets = Decimal(0)
            self.post_fee = Decimal(1 - fee)
            
    def authenticate(self, api_key, api_secret, client):
        self.is_test = False
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = client
        self.fetch_balance_and_assets()
        
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
            #Fetch minor currency value from the exchange
            payload = self.create_authenticated_payload()
            r = requests.post('https://api.quadrigacx.com/v2/balance', data=payload)

            self.balance = Decimal(r.json()[self.minor_currency+"_balance"]) * self.percentage_to_trade
            self.assets = Decimal(r.json()[self.major_currency+"_balance"]) * self.percentage_to_trade
        
    def buy(self, market_value):
        if self.can_buy == True:
        
            if self._waiting_for_order_to_fill != None:
                self.was_order_filled(self._waiting_for_order_to_fill)
                
            #Always spend all the balance. A percentage of it was allocated to the trader at the start.
            assets_to_buy = self.balance / market_value
            if assets_to_buy >= self.minimum_trade:
                
                self._active_buy_order = True
                
                if self.is_test:
                    self.simulation_buy(assets_to_buy)
                else:
                    self.limit_buy_order(market_value)
                
                print("Buying. Planning to spend: "+str(self.balance)+self.minor_currency)
                self.balance = 0
            else:
                sys.stdout.write('b ')
              
    def limit_buy_order(self, market_value):  
        payload = self.create_authenticated_payload()
        payload["book"] = self.product
        payload["amount"] = self.balance / market_value
        payload["price"] = market_value
        r = requests.post('https://api.quadrigacx.com/v2/buy', data=payload)
        self._waiting_for_order_to_fill = r.json()["id"]
                
    def simulation_buy(self, assets_to_buy):
        self._waiting_for_order_to_fill = QuadrigaTrader.simulation_buy_order_id
                    
        # Order will not be "filled" until
        # filled_simulation_assets == expecting_simulation_assets
        self._expecting_simulation_assets = assets_to_buy
        self._filled_simulation_assets = 0
        
        # Only orders that matter are the ones that might fill us which can only
        # happen in the future.
        self._last_simulation_transaction_check = time.time()
        
    def sell(self, market_value):
        if self._waiting_for_order_to_fill != None:
            self.was_order_filled(self._waiting_for_order_to_fill)
            
        if self.can_sell:
            
            #Always sell all assets. A percentage of them was allocated to the trader at the start.
            if self.assets >= self.minimum_trade:
                
                self._active_sell_order = True
                
                if self.is_test:
                    self.simulation_sell(market_value)
                else:
                    self.limit_sell_order(market_value)
                
                print("Selling. Planning to get balance: "+str(self.assets * market_value * self.post_fee)+self.minor_currency)
                self.assets = 0
            else:
                sys.stdout.write('s ')
                
    def limit_sell_order(self, market_value):
        payload = self.create_authenticated_payload()
        payload["book"] = self.product
        payload["amount"] = self.assets
        payload["price"] = market_value
        r = requests.post('https://api.quadrigacx.com/v2/buy', data=payload)
        self._waiting_for_order_to_fill = r.json()["id"]
                
    def simulation_sell(self, market_value):
        self._waiting_for_order_to_fill = QuadrigaTrader.simulation_sell_order_id
                    
        # Order will not be "filled" until
        # _filled_simulation_balance == _expecting_simulation_balance
        self._expecting_simulation_balance = self.assets * market_value
        self._filled_simulation_balance = 0
        
        # Used to track how much balance is earned from partial fills.
        self._limit_order_price = market_value
        
        # Only orders that matter are the ones that might fill us which can only
        # happen in the future.
        self._last_simulation_transaction_check = time.time()
            
    def was_order_filled(self, order_id):
        '''
        Post: Internal balance/assets is updated if the order was filled.
        '''
        
        if self.is_test:
            try:
                assert(order_id == QuadrigaTrader.simulation_buy_order_id or 
                       order_id == QuadrigaTrader.simulation_sell_order_id)
            except AssertionError as e:
                e.args += ("Invalid order ID: ", order_id)
                raise
            
            # Simulate the trader's order being filled by watching what the market.
            # It is likely that simulation mode results in higher profits as in reality
            # other bots undercut our own trades so our orders are filled less frequently.
            
            # The time frame is an hour because the pipeline's polling frequency
            # could be set to be longer than the default number of seconds.
            payload = {"book": self.product, "time": "hour"}
            r = requests.get('https://api.quadrigacx.com/v2/transactions', params=payload)
            
            for trade in r.json():
                if int(trade["date"]) < self._last_simulation_transaction_check:
                    break
                else:
                    with localcontext() as context:
                        context.prec = 8
                        
                        if order_id == QuadrigaTrader.simulation_buy_order_id and trade["side"] == "sell":
                            self._filled_simulation_assets += Decimal(trade["amount"])
                            if self._filled_simulation_assets >= self._expecting_simulation_assets:
                                self.assets = self._expecting_simulation_assets * self.post_fee
                                self._active_buy_order = False
                        elif order_id == QuadrigaTrader.simulation_sell_order_id and trade["side"] == "buy":
                            incoming_balance = Decimal(trade["amount"]) * self._limit_order_price
                            self._filled_simulation_balance += incoming_balance
                            if self._filled_simulation_balance >= self._expecting_simulation_balance:
                                self.balance = self._expecting_simulation_balance * self.post_fee
                                self._active_sell_order = False
            
        else:
            
            # Lookup the order on the market and check its status.
            # The trader will stop if the order was cancelled as a human intervened.
            # Note: The pipeline never knows the Trader's status so the pipeline will continue
            #       to pass data to the market observer.
            
            payload = self.create_authenticated_payload()
            payload[id] = order_id
            r = requests.post('https://api.quadrigacx.com/v2/lookup_order', data=payload)
            json_result = r.json()
            
            
            # Status codes: -1 cancelled, 0 active, 1 = partially filled, 2 = filled
            status_code = json_result["status"]
            if status_code == 2:
                # Type 0 == Buy, Type 1 == Sell
                if json_result["type"] == 0:
                    self.assets = (json_result["price"] * json_result["amount"]) * self.post_fee
                    self._active_buy_order = False
                else:
                    self.balance = (json_result["price"] * json_result["amount"]) * self.post_fee
                    self._active_sell_order = False
            elif status_code == 1:
                print("The order has been partially filled. Waiting until it is fully filled.")
            elif status_code == -1:
                print("The order was cancelled, likely because a human intervened.")
                self._waiting_for_order_to_fill = None
                self.abort()
        
    def create_authenticated_payload(self):
        ''' Pre: API Key, client, and API secret have been set. '''
        nonce = str(int(time.time()*100))
        msg = nonce + self.client + self.api_key
        signature = hmac.new(self.api_secret, msg, hashlib.sha256).hexdigest()
        return {'key': self.api_key, 'nonce': nonce, 'signature': signature}
    
    def cancel_order(self, order_id):
        payload = self.create_authenticated_payload()
        payload["id"] = order_id
        requests.post('https://api.quadrigacx.com/v2/cancel_order', data=payload)
    
    def hold(self, market_value):
        ''' Revert to default position. '''
        if self.default_position:
                
            if self._active_sell_order:
                # Cancel sell order
                if self.is_test:
                    self._waiting_for_order_to_fill = 0
                else:
                    self.cancel_order(self._waiting_for_order_to_fill)
                self._active_sell_order = False
            
            # Buy with any remaining balance
            if self.is_test:
                if self._filled_simulation_balance > 0:
                    self.simulation_buy(self._filled_simulation_balance / market_value)
                    self._active_buy_order = True
            elif self.balance > 0:
                self.limit_buy_order(market_value)
                self._active_buy_order = True

        else:
            if self._active_buy_order:
                # Cancel sell order
                if self.is_test:
                    self._waiting_for_order_to_fill = 0
                else:
                    self.cancel_order(self._waiting_for_order_to_fill)
                self._active_buy_order = False
            
            # Sell any remaining assets
            if self.is_test:
                if self._filled_simulation_assets > 0:
                    self.simulation_sell(market_value)
                    self._active_sell_order = True
            elif self.assets > 0:
                self.limit_sell_order(market_value)
                self._active_sell_order = True
    
    def abort(self):
        Trader.abort(self)
        print("QuadrigaTrader is shutting down.")
    
'''
Uses the Bittrex API to place live and simulation orders.
@author: Tobias Carryer
'''

import datetime
import sys
from decimal import Decimal, localcontext
from cryptotrader import Trader, DefaultPosition
from cryptotrader.bittrex import BittrexSecret
from cryptotrader.librariesrequired.bittrex.bittrex import Bittrex
from cryptotrader.bittrex.bittrex_options import bittrex_minimum_btc_trade_size,\
    bittrex_precision, bittrex_fee

class BittrexTrader(Trader):
        
    simulation_buy_order_id = "1234"
    simulation_sell_order_id = "4321"
        
    def __init__(self, market="BTC-XMR", minimum_trade_size=bittrex_minimum_btc_trade_size, percentage_to_allocate=1, percentage_per_trade=1, starting_amount=1):
        '''
        Pre: options is an instance of QuadrigaOptions and must have pair and ticker set.
        Post: self.is_test = True until authenticate() is called
        '''

        # Trader is in test mode by default.
        # minimum_trade is the minimum amount of assets that can be sold on a trade.
        Trader.__init__(self, True, minimum_trade_size)
        
        # Will be set to a number (order ID) when an order is placed.
        self._waiting_for_order_to_fill = None
        
        # Used to place orders, cancel orders, get the order book during simulation mode
        self.bittrex_api = Bittrex(BittrexSecret.api_key, BittrexSecret.api_secret)
        
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
        
        # These variables determine how much the trader is allowed to trade with and
        # how much it will commit per trade.
        if percentage_to_allocate > 1:
            raise Warning("percentage_to_allocate cannot be greater than 1")
        self.percentage_to_allocate = Decimal(percentage_to_allocate)
        self.percentage_per_trade = Decimal(percentage_per_trade)
        self.validate_percentage_per_trade()
        
        # Get the market ticker and split it up for print statements.
        self.market = market
        self.minor_currency, self.major_currency = market.split("-")
        
        with localcontext() as context:
            context.prec = 8
            
            self.balance = Decimal(starting_amount)
            self.assets = Decimal(0)

            self.fee_added = Decimal(1) + bittrex_fee
            self.fee_substracted = float(1 - bittrex_fee)
            
    def authenticate(self):
        self.is_test = False
        self.fetch_balance_and_assets()
        
    def validate_percentage_per_trade(self):
        if self.percentage_per_trade > 1:
            raise Warning("percentage_per_trade cannot be greater than 1")
        
    def should_default_to(self, default_position):
        '''
        True == hold/buy major currency when the market is unprofitable
        False == hold/sell to get minor currency when market is unprofitable 
        None == hold whatever the trader has
        '''
        self.default_position = default_position
        
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
            #Fetch the two availability of the two currencies from the exchange.
            minor_currency_available = self.bittrex_api.get_balance(self.minor_currency)["result"]["Available"]
            if minor_currency_available == None:
                minor_currency_available = 0
            self.balance = Decimal(float(minor_currency_available)) * self.percentage_to_allocate
            major_currency_available = self.bittrex_api.get_balance(self.major_currency)["result"]["Available"]
            if major_currency_available == None:
                major_currency_available = 0
            self.assets = Decimal(float(major_currency_available)) * self.percentage_to_allocate
            print("Trading with: "+str(round(self.balance, 3))+self.minor_currency+" and "+str(round(self.assets,3))+self.major_currency)
        
    def buy(self, market_value):
        if self.can_buy == True:
        
            if self._waiting_for_order_to_fill != None:
                self.was_order_filled(self._waiting_for_order_to_fill)
                
            # Prevent buying while a sell order is active.
            if self._waiting_for_order_to_fill == None:    
            
                #Only trade the percentage of the balance allocated to a single trade.
                #Bittrex charges its commission on top of the amount requested. (Divide by the fee + 1)
                balance_for_this_buy = (self.balance * self.percentage_per_trade) / self.fee_added
                assets_to_buy = balance_for_this_buy / market_value
                
                assets_to_buy = round(assets_to_buy, bittrex_precision)
                market_value = round(market_value, bittrex_precision)
                if assets_to_buy >= self.minimum_trade:
                    
                    self._active_buy_order = True
                    
                    if self.is_test:
                        self.simulation_buy(assets_to_buy)
                    else:
                        self.limit_buy_order(assets_to_buy, market_value)
                    
                    print("Buying in "+self.market+". Planning to spend: "+str(self.balance)+self.minor_currency)
                    self.balance = Decimal(0)
                else:
                    sys.stdout.write('b ')
                    
            else:
                sys.stdout.write('wb ')
              
    def limit_buy_order(self, quantity, market_value):
        if self.bittrex_api is not None:
            result = self.bittrex_api.buy_limit(self.market, quantity, market_value)
            if result["result"] is not None:
                self._waiting_for_order_to_fill = result["result"]["uuid"]
            self._active_buy_order = True
        else:
            raise Warning("self.bittrex_api cannot be None")
                
    def simulation_buy(self, quantity):
        self._waiting_for_order_to_fill = BittrexTrader.simulation_buy_order_id
                    
        # Order will not be "filled" until
        # filled_simulation_assets == expecting_simulation_assets
        self._expecting_simulation_assets = quantity * float(self.fee_added) 
        self._filled_simulation_assets = 0
        
        # Only orders that matter are the ones that might fill us which can only
        # happen in the future.
        self._last_simulation_transaction_check = datetime.datetime.now()
        
        self._active_buy_order = True
        
    def sell(self, market_value):
        if self.can_sell:
            if self._waiting_for_order_to_fill != None:
                self.was_order_filled(self._waiting_for_order_to_fill)
            
            # Prevent selling while a buy order is active.
            if self._waiting_for_order_to_fill == None:
            
                #Always sell all assets.
                assets_to_sell = round(self.assets, bittrex_precision)
                market_value = round(market_value, bittrex_precision)
                if self.assets >= self.minimum_trade:
                    
                    self._active_sell_order = True
                    
                    if self.is_test:
                        self.simulation_sell(assets_to_sell, market_value)
                    else:
                        self.limit_sell_order(assets_to_sell, market_value)
                    
                    print("Selling. Planning to get balance: "+str(assets_to_sell * market_value * self.fee_substracted)+self.minor_currency)
                    self.assets = Decimal(0)
                else:
                    sys.stdout.write('s ')
                    
            else:
                sys.stdout.write('ws ')
                
    def limit_sell_order(self, quantity, market_value):
        if self.bittrex_api is not None:
            result = self.bittrex_api.sell_limit(self.market, quantity, market_value)
            if result["result"] is not None:
                self._waiting_for_order_to_fill = result["result"]["uuid"]
            self._active_sell_order = True
        else:
            raise Warning("self.bittrex_api cannot be None")
                
    def simulation_sell(self, quantity, market_value):
        self._waiting_for_order_to_fill = BittrexTrader.simulation_sell_order_id
                    
        # Order will not be "filled" until
        # _filled_simulation_balance == _expecting_simulation_balance
        self._expecting_simulation_balance = quantity * market_value
        self._filled_simulation_balance = 0
        
        # Used to track how much balance is earned from partial fills.
        self._limit_order_price = market_value
        
        # Only orders that matter are the ones that might fill us which can only
        # happen in the future.
        self._last_simulation_transaction_check = datetime.datetime.now()
        
        self._active_sell_order = True
            
    def was_order_filled(self, order_id):
        '''
        Post: Internal balance/assets is updated if the order was filled.
        '''
        
        if self.is_test:
            try:
                assert(order_id == BittrexTrader.simulation_buy_order_id or 
                       order_id == BittrexTrader.simulation_sell_order_id)
            except AssertionError as e:
                e.args += ("Invalid order ID: ", order_id)
                raise
            
            # Simulate the trader's order being filled by watching what the market.
            # It is likely that simulation mode results in higher profits as in reality
            # other bots undercut our own trades so our orders are filled less frequently.
            
            history = self.bittrex_api.get_market_history(self.market)["result"]
            
            for trade in history:
                if "." in trade["TimeStamp"]:
                    timestamp = datetime.datetime.strptime(trade["TimeStamp"],"%Y-%m-%dT%H:%M:%S.%f")
                else:
                    timestamp = datetime.datetime.strptime(trade["TimeStamp"],"%Y-%m-%dT%H:%M:%S")
                if timestamp < self._last_simulation_transaction_check:
                    break
                else:
                    with localcontext() as context:
                        context.prec = 8
                        
                        if order_id == BittrexTrader.simulation_buy_order_id and trade["OrderType"] == "SELL":
                            self._filled_simulation_assets += trade["Quantity"]
                            if self._filled_simulation_assets >= self._expecting_simulation_assets:
                                self.assets = self._expecting_simulation_assets * self.fee_substracted
                                self._active_buy_order = False
                                self._waiting_for_order_to_fill = None
                        elif order_id == BittrexTrader.simulation_sell_order_id and trade["OrderType"] == "BUY":
                            incoming_balance = trade["Quantity"] * self._limit_order_price
                            self._filled_simulation_balance += incoming_balance
                            if self._filled_simulation_balance >= self._expecting_simulation_balance:
                                self.balance = self._expecting_simulation_balance * self.fee_substracted
                                self._active_sell_order = False
                                self._waiting_for_order_to_fill = None
                                
            # Orders up to this moment have been processed, don't process them again.
            self._last_simulation_transaction_check = datetime.datetime.now()
            
        else:
            
            # Lookup the order on the market and check its status.
            # The trader will stop if the order was cancelled as a human intervened.
            # Note: The pipeline never knows the Trader's status so the pipeline will continue
            #       to pass data to the market observer.
            
            json_result = self.bittrex_api.get_order(order_id)["result"]
            
            if json_result["CancelInitiated"] == True:
                print("The order was cancelled, likely because a human intervened.")
                self._waiting_for_order_to_fill = None
                self.abort()
            elif json_result["Quantity"] > json_result["Quantity"] - json_result["QuantityRemaining"] > 0:
                print("The order has been partially filled. Waiting until it is fully filled.")
            elif json_result["IsOpen"] == False:
                order_type = json_result["Type"]
                if order_type == "LIMIT_BUY":
                    self.assets = Decimal(json_result["Quantity"] - json_result["CommissionPaid"])
                    self._active_buy_order = False
                    self._waiting_for_order_to_fill = None
                elif order_type == "LIMIT_SELL":
                    self.balance = Decimal((json_result["price"]) * Decimal(json_result["amount"]) - json_result["CommissionPaid"])
                    self._active_sell_order = False
                    self._waiting_for_order_to_fill = None
                else:
                    print "Unexpected order type: " + order_type
    
    def hold(self, market_value):
        ''' Cancel any open orders and revert back to the default position depending on aggressiveness. '''
        
        if self._waiting_for_order_to_fill != None:
            self.was_order_filled(self._waiting_for_order_to_fill)
        
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
        order_info = self.bittrex_api.get_order(order_id)["result"]
        if order_info is not None:
            quantity_remaining = Decimal(order_info["QuantityRemaining"])
            self.balance = (quantity_remaining * Decimal(order_info["Limit"])) - Decimal(order_info["CommissionPaid"])
            self.assets = Decimal(order_info["Quantity"]) - quantity_remaining
            self.bittrex_api.cancel(order_id)
    
    def abort(self):
        Trader.abort(self)
        self._waiting_for_order_to_fill = None
        print("BittrexTrader is shutting down.")
    
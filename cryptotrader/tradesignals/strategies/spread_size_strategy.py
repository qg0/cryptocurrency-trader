'''
This strategy notifies observers when the spread size is large enough to be profitable.
@author: Tobias Carryer
'''

from decimal import Decimal, localcontext

from cryptotrader.tradesignals.strategies import Strategy
from cryptotrader.tradesignals.indicators import SpreadSize
from cryptotrader import DefaultPosition

class SpreadSizeStrategy(Strategy):
    
    def __init__(self, default_position, undercut_market_by=0.01, minimum_return=1.005, market_fee=0.005):
        '''
        default_position is whether the Strategy should hold the minor currency (sell, False) or
        the major currency (buy / True) after scalping the market. For example, in a USD-CAD market
        True would mean CAD is held after scalping and False would mean USD is held after scalping.
        
        It is assumed that the default_position is currently being held. If not, override it by setting
        current_position after initializing the strategy.
        '''
        
        Strategy.__init__(self)
        
        self._spread_size_indicator = SpreadSize(minimum_return, market_fee)
        self.default_position = default_position
        self.current_position = default_position
        self._first_time_unprofitable = True #Prevents repeating the same message.
        
        # undercut_market_by is used to make the strategy's order be the next one filled on the market.
        with localcontext() as context:
            context.prec = 8
            self.undercut_market_by = Decimal(undercut_market_by)

    def process_order_book(self, highest_bid, lowest_ask):
        '''
        Pre: Traders keep track of their balance / assets and do not attempt a trade when they do not
             have the balance to buy with or the assets to sell.
        '''
        
        # Financial calculations need accurate decimals
        with localcontext() as context:
            context.prec = 8
            
            # The spread has to be calculated using the values that the strategy will try to use, not what
            # is already being used.
            highest_bid = Decimal(highest_bid)+self.undercut_market_by
            lowest_ask = Decimal(lowest_ask)-self.undercut_market_by

            if self._spread_size_indicator.is_profitable(highest_bid, lowest_ask):
                
                # Changing current_position causes the trader to vacillate between buying and selling.
                # Traders will not enter a position when the trader does not have the balance/assets
                # so this causes the Trader to wait until their position is exited before they enter the
                # market again - with the opposite position.
                
                if self.current_position:
                    self.notify_observers(False, lowest_ask)
                    self.current_position = False
                else:
                    self.notify_observers(True, highest_bid)
                    self.current_position = True
                self._first_time_unprofitable = True
                    
            else:
                
                # Not profitable = hold default position.
                if self.default_position == DefaultPosition.HOLD:
                    if self._first_time_unprofitable:
                        print("Spread is not profitable. Holding.")
                    self.notify_observers(None, -1) # market_value is irrelevant so it will be set to -1
                else:
                    if self.default_position == DefaultPosition.BUY:
                        if self._first_time_unprofitable:
                            print("Spread is not profitable. Holding major currency.")
                        self.notify_observers(None, lowest_ask)
                    elif self.default_position == DefaultPosition.SELL:
                        if self._first_time_unprofitable:
                            print("Spread is not profitable. Holding minor currency.")
                        self.notify_observers(None, highest_bid)
                    self.current_position = self.default_position
                self._first_time_unprofitable = False
            
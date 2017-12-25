'''
Observes when a strategy says to buy or sell on any market.
It is assumed the strategy does not know what market will be traded.
Will stop after a sell signal.

Ideally, this observer will handle one buy
signal, one sell signal, then stop.

@author Tobias Carryer
'''

from strategy_observer import StrategyObserver
from decimal import Decimal
from cryptotrader.helper_methods import quantity_adjusted_for_decimals

class SingleTradeStrategyObserver(StrategyObserver):
    
    def notify_significant_change(self, should_buy, market_value, market_ticker, amount_to_buy=Decimal(-1)):
        # Have just enough to buy. Assumes the trader determines how much to buy
        # by calculating self.balance / market_value

        if amount_to_buy >= Decimal(0):
            self.trader.balance = quantity_adjusted_for_decimals(amount_to_buy * market_value)
        
        if should_buy == True:
            self.trader.market_ticker = market_ticker
            self.trader.assets = Decimal(0) # Disregard assets for the previous market
            self.trader.buy(market_value)
        elif should_buy == False:
            self.trader.market_ticker = market_ticker
            self.trader.sell(market_value)
            self.trader.abort()
        else:
            self.trader.hold(market_value)
'''
Observes when a strategy says to buy or sell.

@author Tobias Carryer
'''

class MarketChangeObserver(object):
    
    def __init__(self, trader):
        self.trader = trader
    
    def notify_significant_change(self, should_buy, market_value):
        if should_buy:
            self.trader.buy(market_value)
        else:
            self.trader.sell(market_value)
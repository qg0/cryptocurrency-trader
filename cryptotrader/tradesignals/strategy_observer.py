'''
Observes when a strategy says to buy or sell.

@author Tobias Carryer
'''

class StrategyObserver(object):
    
    def __init__(self, trader):
        self.trader = trader
    
    def notify_significant_change(self, should_buy, market_value):
        if should_buy == True:
            self.trader.buy(market_value)
        elif should_buy == False:
            self.trader.sell(market_value)
        else:
            self.trader.hold(market_value)
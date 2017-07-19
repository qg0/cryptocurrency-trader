'''
Observes when data is added to CurrencyHistory.

@author Tobias Carryer
'''

class MarketChangeObserver(object):
    
    def __init__(self, trader):
        self.trader = trader
    
    def notify_significant_change(self, should_buy, market_value):
        if should_buy:
            self.trader.buy(self.trader.percent_to_spend_on_buy, market_value)
        else:
            self.trader.sell(self.trader.percent_of_assets_to_sell, market_value)
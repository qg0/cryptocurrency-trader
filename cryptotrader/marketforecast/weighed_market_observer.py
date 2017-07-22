'''
@author Tobias Carryer
'''

from cryptotrader.marketforecast.market_change_observer import MarketChangeObserver

class WeighedMarketObserver(MarketChangeObserver):
    '''
    Adds ability to weigh losses differently than wins.
    '''
    
    def __init__(self, trader, losses_weight):
        MarketChangeObserver.__init__(self, trader)
        self.spent_on_buys = 0
        self.weighed_net = 0
        self.losses_weight = losses_weight
    
    def notify_significant_change(self, should_buy, market_value):
        if should_buy:
            previous_balance = self.trader.balance
            self.trader.buy(self.trader.percent_to_spend_on_buy, market_value)
            self.spent_on_buys += previous_balance - self.trader.balance
        else:
            previous_balance = self.trader.balance
            self.trader.sell(self.trader.percent_of_assets_to_sell, market_value)
            delta = self.trader.balance - previous_balance
            self.spent_on_buys -= delta
            
            
            if self.spent_on_buys != 0:

                if self.spent_on_buys > 0:
                    #Did not get back everything that was spend
                    self.weighed_net -= self.spent_on_buys * self.losses_weight
                else:
                    self.weighed_net += -self.spent_on_buys
                    
                self.spent_on_buys = 0
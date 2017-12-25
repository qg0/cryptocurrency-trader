'''
Parent object of all other Strategies.
Enables observers to be notified when an action should take place.

@author Tobias Carryer
'''
from cryptotrader.tradesignals.single_trade_strategy_observer import SingleTradeStrategyObserver
from decimal import Decimal

class Strategy(object):
    
    def __init__(self):
        self.observers = []
        
    def attach_observer(self, observer):
        '''
        Post: Observer will be notified when the strategy says to buy or sell.
        Throws: ValueError if observer is None
        '''
        
        if observer == None:
            raise ValueError("observer cannot be None")
        self.observers.append(observer)
        
    def notify_observers(self, should_buy, market_value, market="LTC_BTC", amount_to_buy=Decimal(-1)):
        for observer in self.observers:
            if isinstance(observer, SingleTradeStrategyObserver):
                observer.notify_significant_change(should_buy, market_value, market, amount_to_buy)
            else:
                observer.notify_significant_change(should_buy, market_value)
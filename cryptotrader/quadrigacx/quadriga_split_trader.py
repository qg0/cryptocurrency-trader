'''
Splits trades accross multiple traders so orders are filled faster.
@author: Tobias Carryer
'''

from quadriga_trader import QuadrigaTrader
from quadriga_ignore import QuadrigaSecret
from cryptotrader.tradesignals import StrategyObserver
from cryptotrader.default_position import DefaultPosition

def attach_traders(strategy, options, percent_of_balance_to_trade=1.0, default_position=DefaultPosition.HOLD, aggressive=False, start_by_buying=True, traders=2):
    '''
    Pre: strategy must be a child of Strategy
    Post: strategy has a market observer attached for every trader requested.
    '''
    percent_per_trader = float(percent_of_balance_to_trade) / float(traders)
    
    for _ in range(0, traders):
        trader = QuadrigaTrader(options, percentage_to_trade=percent_per_trader, start_by_buying=start_by_buying)
        trader.should_default_to(default_position, aggressive=aggressive)
        strategy.attach_observer(StrategyObserver(trader))
    
def authenticate_traders(strategy):
    '''
    Pre: strategy must be a child of Strategy
         any traders attached to strategy's observers have to be QuadrigaTraders
    Post: All traders in strategy's observers have been authenticated and are trading live.
    '''
    for observer in strategy.observers:
        if observer.trader is not None:
            observer.trader.authenticate(QuadrigaSecret.api_key, QuadrigaSecret.api_secret, QuadrigaSecret.client_id)
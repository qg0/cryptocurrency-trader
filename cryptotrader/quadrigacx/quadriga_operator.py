'''
This is the file a human should run to trade on QuadrigaCX.
'''

from quadriga_split_trader import attach_traders, authenticate_traders
from cryptotrader.tradesignals.indicators import SpreadSize
from cryptotrader.tradesignals.strategies.spread_size_strategy import SpreadSizeStrategy
from cryptotrader.quadrigacx import QuadrigaTickers, QuadrigaOptions, QuadrigaPipeline
from cryptotrader import DefaultPosition
from decimal import Decimal

# Set the options in one place to make it simple to edit later.
# These are used in trade()
options = QuadrigaOptions(QuadrigaTickers.BTC_USD)
minimum_return = 1.01
percentage_to_trade = 0.5
number_of_traders = 2
is_simulation = False
start_by_buying = True
aggressive = False
default_position = DefaultPosition.BUY
options.undercut = 1

def trade():
    strategy = SpreadSizeStrategy(default_position, minimum_return=minimum_return, market_fee=options.fee, undercut_market_by=options.undercut)
    attach_traders(strategy, options,
                   percent_of_balance_to_trade=percentage_to_trade,
                   default_position=default_position,
                   aggressive=aggressive,
                   start_by_buying=start_by_buying,
                   traders=number_of_traders)
    
    # Sensitive authentication information is kept in a secret file off GitHub.
    if not is_simulation:
        authenticate_traders(strategy)
     
    def on_order_book(bids, asks):
        strategy.process_order_book(bids, asks)
                     
    pipeline = QuadrigaPipeline(on_order_book, options.ticker)
    pipeline.start()
    
def what_is_profitable():
    tickers = [QuadrigaTickers.BTC_CAD, QuadrigaTickers.BTC_USD, QuadrigaTickers.ETH_BTC,
               QuadrigaTickers.ETH_CAD, QuadrigaTickers.LTC_CAD]
    
    something_was_profitable = False
    
    for ticker in tickers:
        
        _options = QuadrigaOptions(ticker)
    
        spread_size_indicator = SpreadSize(minimum_return=1, market_fee=_options.fee)
                        
        # Get the order book once rather than turning on the pipeline.
        order_book = QuadrigaPipeline(None, ticker).get_order_book()
        bids = order_book["bids"]
        asks = order_book["asks"]
        
        highest_bid = Decimal(float(bids[0][0])+_options.undercut)
        lowest_ask = Decimal(float(asks[0][0])-_options.undercut)
        is_profitable = spread_size_indicator.is_profitable(highest_bid, lowest_ask)
        
        if is_profitable:
            something_was_profitable = True
            spread = lowest_ask - highest_bid
            roi = (spread_size_indicator.keep_after_fee_squared + spread_size_indicator.keep_after_fee_squared * spread / highest_bid) - 1
            roi *= 100
            print( ticker + " is profitable. Expected return: " + str(round(roi, 3)) + "%")
            
    if not something_was_profitable:
        print("Nothing is profitable right now.")


if __name__ == "__main__":
    #what_is_profitable()
    trade()
    

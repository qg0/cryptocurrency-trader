'''
This is the file a human should run to trade on QuadrigaCX.
'''

from cryptotrader.tradesignals.observers import MarketChangeObserver
from cryptotrader.tradesignals.strategies.spread_size_strategy import SpreadSizeStrategy
from cryptotrader.quadrigacx import QuadrigaTickers, QuadrigaOptions, QuadrigaPipeline, QuadrigaTrader
from cryptotrader.quadrigacx.quadriga_ignore import QuadrigaSecret

if __name__ == "__main__":

    # Set up the options in one place to make it simple to edit later.
    options = QuadrigaOptions(QuadrigaTickers.BTC_USD)
    minimum_return = 1.005
    percentage_to_trade = 0.1
    default_position = True

    # Sensitive authentication information is kept in a secret file off GitHub.
    trader = QuadrigaTrader(options, default_position=default_position,
                            percentage_to_trade=percentage_to_trade)
    trader.authenticate(QuadrigaSecret.api_key, QuadrigaSecret.api_secret, QuadrigaSecret.client_id)
    
    strategy = SpreadSizeStrategy(default_position, minimum_return=minimum_return, undercut_market_by=options.undercut)
    strategy.attach_observer(MarketChangeObserver(trader))
    
    def on_order_book(bids, asks):
        strategy.process_order_book(bids, asks)
                    
    pipeline = QuadrigaPipeline(on_order_book, options.ticker)
    pipeline.start()
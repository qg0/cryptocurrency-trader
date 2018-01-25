'''
This is the file a human should run to trade on Cryptopia.
'''

from cryptotrader.tradesignals.strategies import SpreadSizeStrategy, FastMarketBuyTool
from cryptotrader.cryptopia.cryptopia_ignore import CryptopiaSecret
from cryptotrader.cryptopia import CryptopiaTrader, CryptopiaPipeline, cryptopia_fee
from cryptotrader import DefaultPosition
from cryptotrader.tradesignals import StrategyObserver, SingleTradeStrategyObserver

# Set the options in one place to make it simple to edit later.
# These are used in trade()
trading_pair = "GRN_BTC"
minimum_return = 1.01
percentage_to_trade = 1
is_simulation = False
start_by_buying = False
aggressive = False
default_position = DefaultPosition.BUY
undercut = 0.00000001

def trade():
    trader = CryptopiaTrader(trading_pair, percentage_to_trade=percentage_to_trade, start_by_buying=start_by_buying)
    
    # Sensitive authentication information is kept in a secret file off GitHub.
    if not is_simulation:
        trader.authenticate(CryptopiaSecret.api_key, CryptopiaSecret.api_secret)
    
    strategy = SpreadSizeStrategy(default_position, minimum_return=minimum_return, market_fee=cryptopia_fee, undercut_market_by=undercut)
    def on_order_book(bids, asks):
        strategy.process_order_book(bids[0]["Price"], asks[0]["Price"])
    strategy.attach_observer(StrategyObserver(trader))
                     
    pipeline = CryptopiaPipeline(on_order_book, trading_pair)
    pipeline.start()
    
def fast_market_buy():
    trader = CryptopiaTrader(trading_pair, percentage_to_trade=percentage_to_trade, start_by_buying=True)
    # Sensitive authentication information is kept in a secret file off GitHub.
    if not is_simulation:
        trader.authenticate(CryptopiaSecret.api_key, CryptopiaSecret.api_secret)
        
    def get_asks(market_ticker):
        def on_order_book(bids, asks):
            print("Did not expect on_order_book to be called while in market order mode.")
        pipeline = CryptopiaPipeline(on_order_book, market_ticker)
        return pipeline.get_order_book()["Sell"]

    strategy = FastMarketBuyTool(get_asks, trading_fee=cryptopia_fee, balance_to_spend=trader.balance)
    strategy.attach_observer(SingleTradeStrategyObserver(trader))
    strategy.start_listening()

if __name__ == "__main__":
    #trade()
    fast_market_buy()
    

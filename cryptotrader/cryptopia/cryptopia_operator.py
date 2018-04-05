'''
This is the file a human should run to trade on Cryptopia.
'''

from cryptotrader.twitter_api_ignore import TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
from cryptotrader.tradesignals.strategies import SpreadSizeStrategy, McAfeeStrategy, FastMarketBuyTool
from cryptotrader.cryptopia.cryptopia_ignore import CryptopiaSecret
from cryptotrader.cryptopia import CryptopiaTrader, CryptopiaPipeline, cryptopia_fee
from cryptotrader.tradesignals.indicators import Twitter
from cryptotrader import DefaultPosition
from cryptotrader.tradesignals import StrategyObserver, SingleTradeStrategyObserver
from decimal import Decimal

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
    
def mcafee_pump(target_profit):
    trader = CryptopiaTrader(trading_pair, percentage_to_trade=percentage_to_trade, start_by_buying=True)
    # Sensitive authentication information is kept in a secret file off GitHub.
    if not is_simulation:
        trader.authenticate(CryptopiaSecret.api_key, CryptopiaSecret.api_secret)
        
    def get_asks(market_ticker):
        def on_order_book(bids, asks):
            print("Did not expect on_order_book to be called while in McAfee pump mode.")
        pipeline = CryptopiaPipeline(on_order_book, market_ticker)
        return pipeline.get_order_book()["Sell"]

    twitter = Twitter(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET,
                      TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
    strategy = McAfeeStrategy(twitter, get_asks, trading_fee=cryptopia_fee,
                              target_profit=target_profit, balance_to_spend=trader.balance)
    strategy.attach_observer(SingleTradeStrategyObserver(trader))
    strategy.start_listening()
    
def fast_market_buy(target_profit):
    trader = CryptopiaTrader(trading_pair, percentage_to_trade=percentage_to_trade, start_by_buying=True)
    # Sensitive authentication information is kept in a secret file off GitHub.
    if not is_simulation:
        trader.authenticate(CryptopiaSecret.api_key, CryptopiaSecret.api_secret)
        
    def get_asks(market_ticker):
        def on_order_book(bids, asks):
            print("Did not expect on_order_book to be called while in market order mode.")
        pipeline = CryptopiaPipeline(on_order_book, market_ticker)
        return pipeline.get_order_book()["Sell"]

    strategy = FastMarketBuyTool(get_asks, trading_fee=cryptopia_fee,
                              target_profit=target_profit, balance_to_spend=trader.balance)
    strategy.attach_observer(SingleTradeStrategyObserver(trader))
    strategy.start_listening()

if __name__ == "__main__":
    #trade()
    #mcafee_pump(target_profit=Decimal(1.75))
    fast_market_buy(target_profit=Decimal(1.22))
    

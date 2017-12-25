''' This is the file a human should run to trade on Bittrex. '''

from cryptotrader.bittrex import BittrexSecret
from cryptotrader.librariesrequired.bittrex.bittrex import Bittrex
from cryptotrader import DefaultPosition
from decimal import Decimal
from cryptotrader.tradesignals.indicators import SpreadSize
from cryptotrader.tradesignals.strategies.spread_size_strategy import SpreadSizeStrategy
from cryptotrader.bittrex.bittrex_pipeline import BittrexPipeline
from cryptotrader.bittrex.bittrex_options import bittrex_fee, bittrex_btc_undercut,\
    bittrex_eth_undercut, bittrex_usd_undercut
from cryptotrader.tradesignals.strategy_observer import StrategyObserver
from cryptotrader.bittrex import BittrexTrader
from cryptotrader.tradesignals.strategies.investing_dot_com_strategy import InvestingDotComStrategy
    
# Set the options in one place to make it simple to edit later.
# These are used in trade()

is_simulation = True
percentage_to_allocate = 0.2

single_market = "BTC-ETH" #Doesn't matter if multi-market trader
minor_currency = "BTC" #Doesn't matter if single market trader
minimum_return = 1.01
default_position = DefaultPosition.SELL
undercut = bittrex_eth_undercut + Decimal(0.0000009)

def trade_single_market_spread():
    trader = BittrexTrader(percentage_to_allocate=percentage_to_allocate, market=single_market)
    trader.should_default_to(default_position)
    if not is_simulation:
        trader.authenticate()
    
    strategy = SpreadSizeStrategy(default_position, minimum_return=minimum_return, market_fee=bittrex_fee, undercut_market_by=undercut)
    strategy.attach_observer(StrategyObserver(trader))
     
    def on_market_summary(market_summary, market):
        strategy.process_order_book(market_summary["Bid"], market_summary["Ask"])
                     
    pipeline = BittrexPipeline(on_market_summary, minor_currency=minor_currency)
    pipeline.start_singlemarket(single_market)
        
def trade_investing_dot_com_strategy(market_url):
    trader = BittrexTrader(percentage_to_allocate=percentage_to_allocate, market=single_market)
    trader.should_default_to(default_position)
    if not is_simulation:
        trader.authenticate()
    
    strategy = InvestingDotComStrategy(market_url, undercut=undercut)
    strategy.attach_observer(StrategyObserver(trader))
     
    def on_market_summary(market_summary, market):
        strategy.get_trading_signal(market_summary["Bid"], market_summary["Ask"])
                     
    pipeline = BittrexPipeline(on_market_summary, minor_currency=minor_currency, poll_time=300)
    pipeline.start_singlemarket(single_market)
    
def what_is_profitable():
    
    spread_size_indicator = SpreadSize(minimum_return=1, market_fee=bittrex_fee)
    
    # Get the markets using a library.
    market_summaries = Bittrex(BittrexSecret.api_key, BittrexSecret.api_secret).get_market_summaries()
    something_was_profitable = False
    for market_summary in market_summaries["result"]:
        if market_summary != None:
            if market_summary["MarketName"].startswith("ETH"):
                _undercut = bittrex_eth_undercut
            elif market_summary["MarketName"].startswith("BTC"):
                _undercut = bittrex_btc_undercut
            else:
                _undercut = bittrex_usd_undercut
            highest_bid = Decimal(market_summary["Bid"])+_undercut
            lowest_ask = Decimal(market_summary["Ask"])-_undercut
            is_profitable = spread_size_indicator.is_profitable(highest_bid, lowest_ask)
            
            if is_profitable:
                something_was_profitable = True
                spread = lowest_ask - highest_bid
                roi = (spread_size_indicator.keep_after_fee_squared + spread_size_indicator.keep_after_fee_squared * spread / highest_bid) - 1
                roi *= 100
                print( market_summary["MarketName"] + " is profitable. Expected return: " + str(round(roi, 3)) + "%")    
    
    if something_was_profitable == False:
        print("Nothing is profitable right now.")
    
if __name__ == "__main__":
    #what_is_profitable()
    #trade_single_market_spread()
    trade_investing_dot_com_strategy("https://www.investing.com/currencies/eth-btc?cid=1031045")
    

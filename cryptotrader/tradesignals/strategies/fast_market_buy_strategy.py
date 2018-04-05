'''
Wait for the user to enter a coin, then buy it.
It prioritizes speed over emulating a true market order.
@author: Tobias Carryer
'''

from cryptotrader.tradesignals.strategies import Strategy
from decimal import Decimal
from cryptotrader.helper_methods import quantity_adjusted_for_decimals
from time import sleep

class FastMarketBuyTool(Strategy):
    '''
    Uses SingleTradeStrategyObserver
    '''
    
    def __init__(self, get_asks, balance_to_spend, trading_fee=Decimal(0.002), max_price_dif=Decimal(1.35), target_profit=Decimal(1.50), price_key="Price", volume_key="Volume", ticker_format="REPLACE_BTC"):
        '''
        get_asks must return an array where each entry are the asks are in
            ascending order. Each entry in the array is a dictionary with the
            values price_key and volume_key which return the price and amount
            being sold respectively. The method must take the ticker as a parameter.
        ticker_format uses the keyword "REPLACE" as where to insert the coin to buy
        '''
        Strategy.__init__(self)
        self.get_asks = get_asks
        self.balance_to_spend = balance_to_spend
        self.post_fee = Decimal(1) - trading_fee
        self.price_key = price_key
        self.volume_key = volume_key
        self.ticker_format = ticker_format
        self.target_profit = target_profit
        self.max_price_dif = max_price_dif
        print("Created Fast Market Buy Strategy.")
        print("This strategy simulates a market buy using limit orders.")
        print("The 'Buying' message outputted by the bot will have an incorrect amount to spend.")
        print("This is because the bot is emulating a market order through a limit order.")
        
    def start_listening(self):
        retry = True
        
        while retry:
            try:
                coin = raw_input("Enter the coin to market buy:").upper()
                
                market_ticker = self.ticker_format.replace("REPLACE", coin)
                asks = self.get_asks(market_ticker)
                lowest_ask = Decimal(asks[0][self.price_key])
                target_ask = lowest_ask * self.max_price_dif
                target_ask = quantity_adjusted_for_decimals(target_ask)
                amount_to_buy = (self.balance_to_spend / target_ask) * self.post_fee
                amount_to_buy = quantity_adjusted_for_decimals(amount_to_buy)
                self.notify_observers(True, target_ask, market=market_ticker, amount_to_buy=amount_to_buy)
                sleep(5)
                profit_ask = quantity_adjusted_for_decimals((lowest_ask+target_ask)/2 * self.target_profit)
                self.notify_observers(False, profit_ask, market=market_ticker)
                retry = False
            except TypeError:
                print("Invalid coin ticker.")
        
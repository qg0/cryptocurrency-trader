'''
Watch McAfee's Twitter account for the "Coin of the day"
@author: Tobias Carryer
'''

import re
from cryptotrader.tradesignals.strategies import Strategy
from decimal import Decimal
from cryptotrader.helper_methods import quantity_adjusted_for_decimals

# The user ID as fetched from http://gettwitterid.com
MCAFEE_USER_ID = "961445378"

class McAfeeStrategy(Strategy):
    '''
    Uses SingleTradeStrategyObserver
    '''
    
    def __init__(self, twitter, get_asks, balance_to_spend, trading_fee=Decimal(0.002), target_profit=Decimal(1.50), price_key="Price", volume_key="Volume", ticker_format="REPLACE_BTC"):
        '''
        Parameters are the API information necessary to connect to Twitter.
        get_asks must return an array where each entry are the asks are in
            ascending order. Each entry in the array is a dictionary with the
            values price_key and volume_key which return the price and amount
            being sold respectively. The method must take the ticker as a parameter.
        ticker_format uses the keyword "REPLACE" as where to insert the coin to buy
        '''
        Strategy.__init__(self)
        self.twitter = twitter
        self.get_asks = get_asks
        self.balance_to_spend = balance_to_spend
        self.post_fee = Decimal(1) - trading_fee
        self.price_key = price_key
        self.volume_key = volume_key
        self.ticker_format = ticker_format
        self.target_profit = target_profit
        print("Created McAfee strategy.")
        print("The 'Buying' message outputted by the bot will have an incorrect amount to spend.")
        print("This is because the bot is emulating a market order through a limit order.")
    
    def on_coin_of_the_day(self, tweet_text):
        # All McAfee's "Coin of the day" tweets have "Coin of the day" at the start
        # However, it is possible he may change the capitalization at some point by
        # accident. Change the tweet to lower case to prevent this problem.
        tweet_text = tweet_text.lower()
        if tweet_text.startswith("coin of the day:"):
            # group 0 includes the parentheses
            coin = re.search("\((\w{1,4})\)", tweet_text).group(1)
            market_ticker = self.ticker_format.replace("REPLACE", coin)
            asks = self.get_asks(market_ticker)
            highest_ask = Decimal(0)
            amount_to_buy = Decimal(0)
            for ask in asks:
                # Slightly over bid no matter what since the market will be moving fast
                price = Decimal(ask[self.price_key]) + Decimal(0.00000001)
                amount_being_sold = Decimal(ask[self.volume_key])
                spendable = price * amount_being_sold
                
                if price > highest_ask:
                    highest_ask = price
                
                if spendable > self.balance_to_spend:
                    amount_to_buy += self.balance_to_spend / (price+Decimal(0.00000001))
                    break
                else:
                    self.balance_to_spend -= spendable
                    amount_to_buy += amount_being_sold
            amount_to_buy = quantity_adjusted_for_decimals(amount_to_buy)
            highest_ask = quantity_adjusted_for_decimals(highest_ask)
                
            # Buy the coin McAfee tweeted out,
            # wait a minute for the order to fill,
            # then place a sell order.
            #self.notify_observers(True, highest_ask, market=market_ticker, amount_to_buy=amount_to_buy)
            print("McAfee tweeted: %s" % tweet_text)
            #sleep(60)
            self.observers[0].trader.assets = Decimal(99.76764706)
            target_ask = quantity_adjusted_for_decimals(highest_ask * self.target_profit)
            self.notify_observers(False, target_ask, market=market_ticker)
        else:
            print("Skipping tweet by McAfee: %s" % tweet_text)
            
    def start_listening(self):
        self.twitter.start_streaming(MCAFEE_USER_ID, self.on_coin_of_the_day)
        
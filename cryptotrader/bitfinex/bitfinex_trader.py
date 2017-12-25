'''
Makes sure all the other general classes work on the Bitfinex.

@author: Tobias Carryer
'''

from cryptotrader.tradesignals import StrategyObserver
from cryptotrader.tradesignals.strategies import SarStrategy
from cryptotrader.trader import Trader
from cryptotrader.bitfinex import BitfinexPipeline

class BitfinexTrader(Trader):
        
    def __init__(self, is_test, minimum_trade):
        Trader.__init__(self, is_test, minimum_trade)
        if is_test:
            self.balance = 100
            self.assets = 0
        else:
            self.balance = self.fetch_balance()
            self.assets = self.fetch_assets()
        
    def buy(self, market_value):
        if self.can_buy:
            #Determine how much will be spent
            currency_to_spend = self.balance
            
            if currency_to_spend > self.minimum_trade:
                #Keep track internally of assets and balance alloted to this bot
                self.balance -= currency_to_spend
                self.assets += currency_to_spend / market_value

                if not self.is_test:
                    #Todo, Send order to the exchange
                    pass
                
                print("Buying. Spent: "+str(currency_to_spend))
            else:
                print("Not enough balance to buy.")
        
    def sell(self, market_value):   
        #Determine how many assets will be sold
        assets_to_sell = self.assets
        
        if assets_to_sell > 0:
            #Keep track internally of assets and balance, simulation purposes only
            self.assets -= assets_to_sell
            self.balance += assets_to_sell * market_value
            
            #Todo, Send order to the exchange
            
            print("Selling. Gained: "+str(assets_to_sell * market_value))
        
    def fetch_balance(self):
        '''
        Get the balance this trader has permission to spend in the exchange.
        '''
        
        if self.is_test:
            print("Warning: fetch_balance was called when trader is in test mode.")
            return self.balance
        else:
            #Todo, fetch wallet value from the exchange
            pass
        
    def fetch_assets(self):
        '''
        Get the number of assets this trader has permission to sell in the exchange.
        '''
        
        if self.is_test:
            print("Warning: fetch_assets was called when trader is in test mode.")
            return self.assets
        else:
            #Todo, fetch assets from the exchange
            pass

#Test the Bitfinex bot on historical data by running this file.

if __name__ == "__main__":
              
    #Real-time data test
    trader = BitfinexTrader(True, 0.01)
    strategy = SarStrategy()
    strategy.attach_observer(StrategyObserver(trader))
    data_points_per_period = 300
                  
    def on_market_value(value):
        strategy.process_pipeline_data(value, data_points_per_period)
                   
    pipeline = BitfinexPipeline(on_market_value, "LTCBTC", True)
    pipeline.start()
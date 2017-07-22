'''
Makes sure all the other general classes work on the GDAX.

@author: Tobias Carryer
'''

from cryptotrader.marketforecast.market_change_observer import MarketChangeObserver
from cryptotrader.marketforecast.currency_history import CurrencyHistory
from cryptotrader.trader import Trader
from cryptotrader.gdax.gdax_pipeline import GDAXPipeline

class GDAXTrader(Trader):
        
    def __init__(self, is_test, minimum_trade):
        Trader.__init__(self, is_test, minimum_trade)
        if is_test:
            self.balance = 1000
            self.assets = 0
        else:
            self.balance = self.fetch_balance()
            self.assets = self.fetch_assets()
        
    def buy(self, percent_to_spend, market_value):
        if self.can_buy:
            #Guarantee the amount is positive
            if percent_to_spend < 0:
                raise ValueError("Cannot buy a negative amount.")
                
            #Determine how much will be spent
            currency_to_spend = self.balance * percent_to_spend
            
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
        
    def sell(self, percent_to_sell, market_value):
        #Guarantee the amount is positive
        if percent_to_sell < 0:
            raise ValueError("Cannot buy a negative amount.")
            
        #Determine how many assets will be sold
        if self.sell_all_assets:
            assets_to_sell = self.assets
        else:
            assets_to_sell = self.assets * percent_to_sell
        
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

#Test the GDAX bot on historical data by running this file.
if __name__ == "__main__":
    trader = GDAXTrader(True, 30)
    history = CurrencyHistory(5, 10)
    history.attach_observer(MarketChangeObserver(trader))
    
    #Historical Data Test
    historical_data = GDAXPipeline().load_historical_data()
    
    #Create the trends based on historical data.
    trader.can_buy = False
    #Skip the start of the data since it won't affect the moving averages.
    for index in range(1000000, len(historical_data[0])-2000000):
        value = historical_data[0][index]
        if value < trader.outlier_threshold:
            history.adjust(value, historical_data[1][index])
            
    #Trade using the trends on data closer to the present.
    trader.can_buy = True
    for index in range(len(historical_data[0])-2000000, len(historical_data[0])-100000):
        value = historical_data[0][index]
        if value < trader.outlier_threshold:
            history.adjust(value, historical_data[1][index])
            
    #Stop and give the trader enough time to find a moment to sell but save the last
    #recorded valuation just in case assets' value needs to be calculated.
    trader.can_buy = False
    trader.sell_all_assets = True
    end_value = 0
    
    for index in range(len(historical_data[0])-100000, len(historical_data[0])):
        value = historical_data[0][index]
        #Exclude abnormal valuations.
        if value < trader.outlier_threshold:
            history.adjust(value, historical_data[1][index])
            end_value = value
            
    print("Remaining Balance: " + str(trader.balance))
    print("Assets Value: " + str(trader.assets * end_value))
    print("Net: "+str(trader.balance+(trader.assets * end_value)-1000))
    print("Time elapsed (in seconds): "+str((historical_data[1][len(historical_data[0])-100000] - historical_data[1][len(historical_data[0])-3000000])/1000.0))
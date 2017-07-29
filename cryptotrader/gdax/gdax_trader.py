'''
Makes sure all the other general classes work on the GDAX.

@author: Tobias Carryer
'''

from cryptotrader.tradesignals.market_change_observer import MarketChangeObserver
from cryptotrader.tradesignals.moving_average_strategy import MovingAverageStrategy
from cryptotrader.trader import Trader
from cryptotrader.gdax.gdax_pipeline import GDAXPipeline, load_historical_data

class GDAXTrader(Trader):
        
    def __init__(self, is_test, minimum_trade):
        Trader.__init__(self, is_test, minimum_trade)
        if is_test:
            self.balance = 1000
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

#Test the GDAX bot on historical data by running this file.
if __name__ == "__main__":
    
    #Historical data test
    trader = GDAXTrader(True, 30)
      
    #Historical Data Test
    historical_data = load_historical_data()
     
    #Create the trends based on historical data.
    trader.can_buy = False
    
    #Average difference between timestamps = how often data is saved, and how often it should be processed
    seconds_between_timestamps = 0
    entries_processed = 0
    for index in range(999990, 1000000):
        entries_processed += 1
        delta = historical_data[1][index] - historical_data[1][index-1]
        seconds_between_timestamps = (seconds_between_timestamps + delta) / entries_processed
    
    data_points_per_minute = 60 / seconds_between_timestamps
    
    #Initial EMA in testing mode is just zero since the strategy is passed historical data to
    #calculate the EMA anyway. In a real scenario it should be fetched from another platform.
    initial_ema = 0
    strategy = MovingAverageStrategy(initial_ema, 2, initial_ema, 8, data_points_per_minute)
    strategy.attach_observer(MarketChangeObserver(trader))
    
    #Calculate the EMA
    for index in range(1000000, len(historical_data[0])-2000000):
        value = historical_data[0][index]
        if value < trader.outlier_threshold:
            strategy.adjust(value)
            
    #Trade using the trends on data closer to the present.
    trader.can_buy = True
    for index in range(len(historical_data[0])-2000000, len(historical_data[0])-100000):
        value = historical_data[0][index]
        if value < trader.outlier_threshold:
            strategy.adjust(value)
            
    #Stop and give the trader enough time to find a moment to sell but save the last
    #recorded valuation just in case assets' value needs to be calculated.
    trader.can_buy = False
    trader.sell_all_assets = True
    end_value = 0
    
    for index in range(len(historical_data[0])-100000, len(historical_data[0])):
        value = historical_data[0][index]
        #Exclude abnormal valuations.
        if value < trader.outlier_threshold:
            strategy.adjust(value)
            end_value = value
            
    print("Remaining Balance: " + str(trader.balance))
    print("Assets Value: " + str(trader.assets * end_value))
    print("Net: "+str(trader.balance+(trader.assets * end_value)-1000))
    print("Time elapsed (in seconds): "+str((historical_data[1][len(historical_data[0])-100000] - historical_data[1][len(historical_data[0])-3000000])))
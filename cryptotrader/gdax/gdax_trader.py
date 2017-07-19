'''
Makes sure all the other general classes work on the GDAX.

@author: Tobias Carryer
'''

from cryptotrader.marketforecast.market_change_observer import MarketChangeObserver
from cryptotrader.marketforecast.currency_history import CurrencyHistory
from cryptotrader.trader import Trader
from cryptotrader.gdax.gdax_pipeline import GDAXPipeline

class GDAXTrader(Trader):
        
    def __init__(self):
        Trader.__init__(self)
        self.balance = 1000
        
    def buy(self, percent_to_spend, market_value):
        if self.can_buy:
            #Guarantee the amount is positive
            if percent_to_spend < 0:
                raise ValueError("Cannot buy a negative amount.")
                
            #Determine how much USD will be spent
            currency_to_spend = self.get_balance() * percent_to_spend
            
            #TODO CHECK THAT CURRENCY TO SPEND IS ABOVE THE MARKET'S MINIMUM TRADE REQUIREMENT
            #if currency_to_spend > some hard coded number or fetched number
            
            #Keep track internally of assets and balance, simulation purposes only
            self.balance -= currency_to_spend
            self.assets += currency_to_spend / market_value
            
            #Send order to the exchange
            
            print("Buying. Spent: "+str(currency_to_spend))
        
    def sell(self, percent_to_sell, market_value):
        #Guarantee the amount is positive
        if percent_to_sell < 0:
            raise ValueError("Cannot buy a negative amount.")
            
        #Determine how many assets will be sold
        if self.sell_all_assets:
            assets_to_sell = self.get_assets()
        else:
            assets_to_sell = self.get_assets() * percent_to_sell
        
        if assets_to_sell > 0:
            #Keep track internally of assets and balance, simulation purposes only
            self.assets -= assets_to_sell
            self.balance += assets_to_sell * market_value
            
            #Send order to the exchange
            
            print("Selling. Gained: "+str(assets_to_sell * market_value))
        
    def get_balance(self):
        #Todo, fetch wallet value from the exchange
        return self.balance

#Allow this file to be run to trade on the GDAX
trader = GDAXTrader()
history = CurrencyHistory(8, 13)
history.attach_observer(MarketChangeObserver(trader))

#Historical Data Test
historical_data = GDAXPipeline().load_historical_data()

end_value = 0
trader.can_buy = False
for index in range(0, len(historical_data[0])-950000):
    value = historical_data[0][index]
    #Exclude abnormal valuations.
    if value < trader.outlier_threshold:
        history.adjust(value, historical_data[1][index])
        
trader.can_buy = True
for index in range(len(historical_data[0])-950000, len(historical_data[0])-50000):
    value = historical_data[0][index]
    #Exclude abnormal valuations.
    if value < trader.outlier_threshold:
        history.adjust(value, historical_data[1][index])
trader.can_buy = False
trader.sell_all_assets = True
for index in range(len(historical_data[0])-50000, len(historical_data[0])):
    value = historical_data[0][index]
    #Exclude abnormal valuations.
    if value < trader.outlier_threshold:
        history.adjust(value, historical_data[1][index])
        end_value = value
        
print("Remaining Balance: " + str(trader.balance))
print("Assets Value: " + str(trader.assets * end_value))
print("Net: "+str(trader.balance+(trader.assets * end_value)-1000))

print("Time elapsed (in seconds): "+str((historical_data[1][len(historical_data[0])-5001] - historical_data[1][len(historical_data[0])-950000])/1000.0))
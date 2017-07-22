'''
Machine learning techniques in functions to optimize the GDAX traders.

@author: Tobias Carryer
'''

from cryptotrader.marketforecast.weighed_market_observer import WeighedMarketObserver
from cryptotrader.marketforecast.currency_history import CurrencyHistory
from cryptotrader.gdax.gdax_trader import GDAXTrader
from cryptotrader.gdax.gdax_pipeline import GDAXPipeline

def optimize_gdax_moving_average_length():
    historical_data = GDAXPipeline().load_historical_data()
    
    output = ""
    
    for losses_weight in range(1, 4):
        
        scores = []
        short_lengths = []
        long_lengths = []
        
        for long_term_length in range(2, 31):
            for short_term_length in range(long_term_length/2, long_term_length):
                
                print("Long: "+str(long_term_length)+" Short: "+str(short_term_length))
                
                trader = GDAXTrader(True, 30)
                history = CurrencyHistory(short_term_length, long_term_length)
                observer = WeighedMarketObserver(trader, losses_weight)
                history.attach_observer(observer)
                
                #Create the trends based on historical data.
                trader.can_buy = False
                #Skip the start of the data since it won't affect the moving averages.
                for index in range(1000000, len(historical_data[0])-3000000):
                    value = historical_data[0][index]
                    if value < trader.outlier_threshold:
                        history.adjust(value, historical_data[1][index])
                        
                #Trade using the trends on data closer to the present.
                trader.can_buy = True
                for index in range(len(historical_data[0])-3000000, len(historical_data[0])-100000):
                    value = historical_data[0][index]
                    if value < trader.outlier_threshold:
                        history.adjust(value, historical_data[1][index])
                        
                #Stop and give the trader enough time to find a moment to sell.
                trader.can_buy = False
                trader.sell_all_assets = True
                
                for index in range(len(historical_data[0])-100000, len(historical_data[0])):
                    value = historical_data[0][index]
                    #Exclude abnormal valuations.
                    if value < trader.outlier_threshold:
                        history.adjust(value, historical_data[1][index])
                
                scores.append(observer.weighed_net)
                i = len(scores)-1
                while i > 0 and scores[i] > scores[i-1]:
                    tmp = scores[i]
                    scores[i] = scores[i-1]
                    scores[i-1] = tmp
                    i -= 1
                    
                short_lengths.insert(i, short_term_length)
                long_lengths.insert(i, long_term_length)
                
        output += "Optimal settings when using a loss weight of "+str(losses_weight)+"...\n"
        output += "Choice #1 with weighed net "+str(scores[0])+": Short Term Length: "+str(short_lengths[0])+" Long Term Length: "+str(long_lengths[0])+"\n"
        output += "Choice #2 with weighed net "+str(scores[1])+": Short Term Length: "+str(short_lengths[1])+" Long Term Length: "+str(long_lengths[1])+"\n"
        output += "Choice #3 with weighed net "+str(scores[2])+": Short Term Length: "+str(short_lengths[2])+" Long Term Length: "+str(long_lengths[2])+"\n"
            
    print(output)

if __name__ == "__main__":
    optimize_gdax_moving_average_length()
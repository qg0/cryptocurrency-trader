'''
Machine learning techniques in functions to optimize the GDAX traders.

@author: Tobias Carryer
'''

from cryptotrader.tradesignals.weighed_market_change_observer import WeighedMarketObserver
from cryptotrader.tradesignals.moving_average_strategy import MovingAverageStrategy
from cryptotrader.gdax.gdax_trader import GDAXTrader
from cryptotrader.gdax.gdax_pipeline import load_historical_data

def optimize_gdax_moving_average_length():
    historical_data = load_historical_data()
    
    output = ""
    
    for losses_weight in range(1, 4):
        
        scores = []
        short_lengths = []
        long_lengths = []
        
        for long_term_length in range(2, 21):
            for short_term_length in range(1, long_term_length):
                
                print("Long: "+str(long_term_length)+" Short: "+str(short_term_length))
                
                trader = GDAXTrader(True, 30)
                
                #Create the trends based on historical data.
                trader.can_buy = False
                
                #Average difference between timestamps = how often data is saved, and how often it should be processed
                seconds_between_timestamps = 0
                entries_processed = 0
                for index in range(999990, 1000000):
                    entries_processed += 1
                    delta = historical_data[1][index] - historical_data[1][index-1]
                    seconds_between_timestamps = (seconds_between_timestamps + delta) / entries_processed
                
                data_points_per_minute = 60 / seconds_between_timestamps #Potential off by one error here
                
                #Initial EMA in testing mode is just zero since the history object is passed historical data to
                #calculate the EMA anyway. In a real scenario it should be fetched from another platform.
                initial_ema = 0
                history = MovingAverageStrategy(initial_ema, short_term_length, initial_ema, long_term_length, data_points_per_minute)
                observer = WeighedMarketObserver(trader, losses_weight)
                history.attach_observer(observer)
    
                #Calculate the EMA
                for index in range(1000000, len(historical_data[0])-3000000):
                    value = historical_data[0][index]
                    if value < trader.outlier_threshold:
                        history.adjust(value)
                        
                #Trade using the trends on data closer to the present.
                trader.can_buy = True
                for index in range(len(historical_data[0])-3000000, len(historical_data[0])-100000):
                    value = historical_data[0][index]
                    if value < trader.outlier_threshold:
                        history.adjust(value)
                        
                #Stop and give the trader enough time to find a moment to sell.
                trader.can_buy = False
                trader.sell_all_assets = True
                
                for index in range(len(historical_data[0])-100000, len(historical_data[0])):
                    value = historical_data[0][index]
                    #Exclude abnormal valuations.
                    if value < trader.outlier_threshold:
                        history.adjust(value)
                
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
'''
Loads data from GDAX.

@author: Tobias Carryer
'''

class GDAXPipeline(object):
    def __init__(self):
        print("Created GDAX pipeline.")
        
    def load_historical_data(self):
        '''
        Pre: Historical data is in chronological order.
        '''
        
        values = []
        timestamps = []
        trades_at_time = []
        last_timestamp = 0
        
        with open("coinbaseUSD.csv") as f:
            for line in f:
                
                contents = line.split(",")
                timestamp = float(contents[0]) #UNIX Timestamp
                value = float(contents[1])
                    
                #Average value of all trades that happened at the same moment
                #Assumes timestamps are in chronological order
                if timestamp == last_timestamp:
                    index = len(values)-1
                    values[index] = ((values[index] * values[index]) + value) / (trades_at_time[index] + 1)
                    trades_at_time[index] += 1
                elif timestamp > last_timestamp:
                    values.append(value)
                    trades_at_time.append(1)
                    timestamps.append(timestamp)
                else:
                    print("ERROR: Unexpected timestamp "+str(timestamp)+" after "+str(last_timestamp)+". Violates assertion that timestamps / entries in the historical data are in chronological order.")
                
                last_timestamp = timestamp
                
        print("Finished loading historical data.")
        
        return [values, timestamps]
        
    def load_real_time_data(self):
        while True:
            print("Real time data loading")
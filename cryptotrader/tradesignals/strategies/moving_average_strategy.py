'''
This strategy notifies observers when short and long term MAs cross.

@author: Tobias Carryer
'''

from cryptotrader.tradesignals.strategies import Strategy
from cryptotrader.tradesignals.indicators import EMA

class MovingAverageStrategy(Strategy):
    
    def __init__(self, short_term_ema, short_term_length, long_term_ema, long_term_length, data_points_per_minute):
        '''
        short_term_ema and long_term_ema are the exponential moving averages for the currency
        this object is going to track.
        
        short_term_length and long_term_length are measured in days.
        
        data_points_per_minute is how many times adjust() is expected to be called in a minute.
        '''
        
        Strategy.__init__(self)
        
        print("Created MovingAverageStrategy.")
        
        self.long_term_trend = EMA(short_term_ema, 24*short_term_length*data_points_per_minute)
        self.short_term_trend = EMA(long_term_ema, 24*long_term_length*data_points_per_minute)
        self.long_is_above_short = None

    def adjust(self, value):
        '''
        Determine the long term and short term trends by using a moving average.
        Sell when the long term average is higher than the short term average.
        Buy when the short term average is higher than the long term average.
        
        This strategy is known as the double crossover method.
        '''
 
        self.long_term_trend.add_data_point(value)
        self.short_term_trend.add_data_point(value)
        
        if self.long_is_above_short is None:
            self.long_is_above_short = self.long_term_trend.get() > self.short_term_trend.get()
        else:
            long_ma = self.long_term_trend.get()
            short_ma = self.short_term_trend.get()

            #MovingAverage lines crossed
            if self.long_is_above_short and short_ma > long_ma:
                self.notify_observers(True, value)
                self.long_is_above_short = False
            elif not self.long_is_above_short and long_ma > short_ma:
                self.notify_observers(False, value)
                self.long_is_above_short = True

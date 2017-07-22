'''
CurrencyHistory is constructed with moving averages and notifies observers when significant changes occur.
It contains methods to keep its data up to date as time goes on.

@author: Tobias Carryer
'''

from cryptotrader.marketforecast.trend import Trend

class CurrencyHistory(object):
    
    def __init__(self, short_term_length, long_term_length):
        '''
        short_term_length and long_term_length are measured in days.
        '''
        
        print("Created currency history tracker.")
        
        self._observers = []
        
        self.long_term_trend = Trend(short_term_length)
        self.short_term_trend = Trend(long_term_length)
        self.long_is_above_short = None

    def adjust(self, value, timestamp):
        '''
        Determine the long term and short term trends by using a moving average.
        Sell when the long term average is higher than the short term average.
        Buy when the short term average is higher than the long term average.
        
        This strategy is known as a moving average exponential crossover.
        '''
 
        self.long_term_trend.add_data_point(value, timestamp)
        self.short_term_trend.add_data_point(value, timestamp)
        
        if self.long_is_above_short is None and self.long_term_trend.has_enough_data():
            self.long_is_above_short = self.long_term_trend.get_moving_average() > self.short_term_trend.get_moving_average()
        else:
            long_ma = self.long_term_trend.get_moving_average()
            short_ma = self.short_term_trend.get_moving_average()

            #Trend lines crossed
            if self.long_is_above_short and short_ma > long_ma:
                self.notify_observers(True, value)
                self.long_is_above_short = False
            elif not self.long_is_above_short and long_ma > short_ma:
                self.notify_observers(False, value)
                self.long_is_above_short = True
        
    def attach_observer(self, observer):
        '''
        Post: Observer will be notified when new data is passed to CurrencyHistory.
        Throws: ValueError if observer is None
        '''
        
        if observer == None:
            raise ValueError("observer cannot be None")
        self._observers.append(observer)
        
    def notify_observers(self, should_buy, market_value):
        for observer in self._observers:
            observer.notify_significant_change(should_buy, market_value)

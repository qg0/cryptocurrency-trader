'''
This strategy notifies observers when the parabolic SAR states the trend changed
directions and the ADX says the new trend is strong.

@author: Tobias Carryer
'''

from cryptotrader.tradesignals.strategies import Strategy
from cryptotrader.tradesignals.indicators import SAR

class SarStrategy(Strategy):
    
    def __init__(self, initial_sar=None, acceleration_factor=0.2, max_acceleration_factor=2):
        Strategy.__init__(self)
        
        self._initial_sar = initial_sar
        self._sar = SAR(acceleration_factor, max_acceleration_factor)
        
        self.reset_vars_to_process_pipeline()

    def reset_vars_to_process_pipeline(self):
        self.high = 0
        self.low = float("inf")
        self.data_points_in_period = 0

    def process_pipeline_data(self, value, data_points_per_period):
        '''
        data_points_per_period is how many values should be grouped to determine a high
        and low to pass to adjust()
        
        Post: adjust() is called after process_pipeline_data() is called data_points_per_period times
        '''
        
        if value > self.high:
            self.high = value
        if value < self.low:
            self.low = value
        
        self.data_points_in_period += 1
        
        if self.data_points_in_period >= data_points_per_period:
            self.adjust(self.high, self.low, value)
            self.reset_vars_to_process_pipeline()

    def adjust(self, high, low, close):
        if self._sar.is_set_up():
            #Keep assistant indicator updated
            trend_direction = self._sar.adjust(high, low, close)
            
            #Check if the trend changed direction
            if trend_direction != None:
                
                #Tell the observers what to do
                self.notify_observers(trend_direction, close)
        elif self._initial_sar != None:
            self._sar._set_up(self._initial_sar, high, low)
'''
@author: Tobias Carryer
'''

class EMA(object):

    def __init__(self, initial_ema, moving_average_length, data_points_per_minute):
        '''
        initial_ema is the exponential moving average the instant the MovingAverage was created.
        
        moving_average_length is how many minutes should be taken into consideration
        when calculating the MA.
        
        data_points_per_minute is how many times add_data_point() is expected to
        be called in a minute.
        '''
        
        print("Created EMA assistant.")
        
        self.ema = initial_ema
        
        number_of_data_points = 24 * moving_average_length * data_points_per_minute #Hours, minutes, seconds
        self._ema_multiplier = 2 / (number_of_data_points + 1)
        
    def get_moving_average(self):
        return self.ema
    
    def add_data_point(self, value):
        #Weigh how much value changes the EMA so more recent values affect the EMA more.
        self.ema = (value - self.ema) * self._ema_multiplier + self.ema 
'''
@author: Tobias Carryer
'''

class EMA(object):

    def __init__(self, initial_ema, moving_average_length):
        '''
        initial_ema is the exponential moving average the instant the Moving Average was created.
        
        moving_average_length is how many data points should be taken into consideration
        when calculating the MA.
        '''
        
        print("Created EMA assistant.")
        
        self._ema = initial_ema
        
        self._ema_multiplier = 2 / (moving_average_length + 1)
        
    def get(self):
        return self._ema
    
    def add_data_point(self, value):
        #Weigh how much value changes the EMA so more recent values affect the EMA more.
        self._ema = (value - self._ema) * self._ema_multiplier + self._ema
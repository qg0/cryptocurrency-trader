'''
Indicates if a currency or commodity is overbought or oversold.
Invented by George Lane.

@author Tobias Carryer.
'''

class StochasticOscillator(object):
    
    def __init__(self, periods_to_track=14):
        self.periods_to_track = periods_to_track
        self._lows = []
        self._highs = []
        self._oscillator_reading = None
        
    def is_set_up(self):
        '''
        Returns True if get() will not return None
        '''
        
        return self._oscillator_reading != None
    
    def adjust(self, high, low, close):
        self._highs.append(high)
        self._lows.append(low)
        
        #Check enough data has been passed to the oscillator
        if len(self._highs) > self.periods_to_track:
            #Keep number of highs / lows at periods_to_track
            self._highs.pop(0)
            self._lows.pop(0)
            
            #Get the all time high and low of the past [periods_to_track] periods
            high = 0
            for h in self._highs:
                if h > high:
                    high = h
            low = float("inf")
            for l in self._lows:
                if l < low:
                    low = l
                    
            #Calculate the oscillator reading
            self._oscillator_reading = 100 * (close - low) / (high - low)
        
    def get(self):
        if self._oscillator_reading == None:
            print("StochasticOscillator is not set up but get() was called.")
        return self._oscillator_reading
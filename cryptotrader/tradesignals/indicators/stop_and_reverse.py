'''
Indicates when the trend changes direction.
@author Tobias Carryer
'''

class SAR(object):
    
    def __init__(self, acceleration_factor=0.02, max_acceleration_factor=0.2):
        self.af = acceleration_factor
        self.initial_af = acceleration_factor
        self.max_af = max_acceleration_factor
        
        self._sar = None
        self._bull = True
        self._hp = float("inf")
        self._lp = 0
        self._previous_low = float("inf")
        self._previous_previous_low = float("inf")
        self._previous_high = 0
        self._previous_previous_high = 0
        self._first_time_calling_set_up = True
        
    def _set_up(self, high, low):
        '''
        high is the high of a period
        
        low is the low of a period
        '''
        
        if( self._first_time_calling_set_up == True ):
            self._previous_low = low
            self._previous_high = high
            self._first_time_calling_set_up = False
        else:
            self._lp = min(self._previous_low, low)
            self._hp = max(self._previous_high, high)
        
            #https://quant.stackexchange.com/questions/35570/how-do-you-calculate-the-initial-prior-sar-value-in-a-parabolic-sar-over-fx-mark
            if( self._previous_high < high ):
                #Initial PSAR value is the low point when it is in an upward trend
                self._sar = self._lp
                self._bull = True
            else:
                #Initial PSAR value is the high point when it is in a downward trend
                self._sar = self._hp
                self._bull = False
     
    def is_set_up(self):
        return self._sar != None
     
    def adjust(self, high, low):
        '''
        Returns: True if the trend is going up (bull market).
                False if the trend is going down (bear market).
                None if the trend did not change.
        '''
        
        if self.is_set_up() == False:
            self._set_up(high, low)
            return None
        
        if self._bull:
            self._sar = self._sar + self.af * (self._hp - self._sar)
        else:
            self._sar = self._sar + self.af * (self._lp - self._sar)
            
        reverse = False
        if self._bull:
            if low < self._sar:
                self._bull = False
                reverse = True
                self._sar = self._hp
                self._lp = low
                self.af = self.initial_af
        else:
            if high > self._sar:
                self._bull = True
                reverse = True
                self._sar = self._lp
                self._hp = high
                self.af = self.initial_af
        if not reverse:
            if self._bull:
                if high > self._hp:
                    self._hp = high
                    self.af = min(self.af + self.initial_af, self.max_af)
                if self._previous_low < self._sar:
                    self._sar = self._previous_low
                if self._previous_previous_low < self._sar:
                    self._sar = self._previous_previous_low
            else:
                if low < self._lp:
                    self._lp = low
                    self.af = min(self.af + self.initial_af, self.max_af)
                if self._previous_high > self._sar:
                    self._sar = self._previous_high
                if self._previous_previous_high > self._sar:
                    self._sar = self._previous_previous_high

        #Keep track of previous lows and highs
        self._previous_previous_low = self._previous_low
        self._previous_low = low
        self._previous_previous_high = self._previous_high
        self._previous_high = high

        #Return whether or not the trend was reversed and in what direction
        if reverse:
            return self._bull
        else:
            return None
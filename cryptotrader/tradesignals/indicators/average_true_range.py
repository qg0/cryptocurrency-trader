'''
An indicator that measures volatility.
@author: Tobias Carryer
'''

def true_range(high, low, close):
    '''
    Welles Wilder invented TR and defined it as the greatest of the following:
    Method 1: Current High less the current Low
    Method 2: Current High less the previous Close (absolute value)
    Method 3: Current Low less the previous Close (absolute value)
    '''
    
    m1 = high - low
    m2 = abs(high - close)
    m3 = abs(low - close)
    
    return max(m1, m2, m3)
    
class ATR(object):
    
    def __init__(self, periods_per_atr=14):
        self.periods_per_atr = periods_per_atr
        self.initial_true_ranges = []
        self._atr = None
        
    def is_set_up(self):
        return self._atr != None
        
    def adjust(self, high, low, close):
        if not self.is_set_up():
            #Initial ATR is the average of the past true ranges
            self.initial_true_ranges.append(true_range(high, low, close))
            
            if len(self.initial_true_ranges) >= self.periods_per_atr:
                my_sum = 0
                for tr in self.initial_true_ranges:
                    my_sum += tr
                self._atr = my_sum / self.periods_per_atr
        else:
            #Incorporate the current true range into the ATR
            tr = true_range(high, low, close)
            
            #Include the previous ATR to smooth the data
            self._atr = (self._atr * (self.periods_per_atr-1) + tr) / self.periods_per_atr
        
    def get(self):
        if not self.is_set_up():
            print("ATR is not set up but get() was called.")
        return self._atr
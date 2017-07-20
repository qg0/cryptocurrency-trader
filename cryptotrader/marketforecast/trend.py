'''
@author: Tobias Carryer
'''

from cryptotrader.marketforecast.queue import Queue

class Trend(object):

    def __init__(self, moving_average_length):
        '''
        moving_average_length is how many days should be taken into consideration
        when calculating the MA.
        '''
        
        print("Created trend assistant.")
        
        self._ma_length_in_seconds = moving_average_length * 24 * 60 * 60 #Hours, minutes, seconds
        self._sum_of_data = 0.0
        self._numbers_in_sum = Queue()
        self._timestamps = Queue()
        
    def has_enough_data(self):
        '''
        Returns true if this Trend has enough data points to calculate a simple moving average of
        the length specified when initialized.
        '''
        
        #At least 1 data point for every 30 seconds
        return self._numbers_in_sum.size() >= self._ma_length_in_seconds / 1800
        
    def get_moving_average(self):
        return self._sum_of_data / self._numbers_in_sum.size()
    
    def add_data_point(self, value, timestamp):
        '''
        Data points are assumed to be added in chronological order.
        
        Pre: timestamp is measured in milliseconds
        Post: Moving Average takes value into account.
        '''
        
        if not self._timestamps.isEmpty():
            if timestamp < self._timestamps.peek():
                print("Precondition violated. add_data_points expects data in a chronological order. " +str(timestamp) + " is before " + str(self._timestamps.peek()))
                
            #Remove old data point
            if timestamp - self._timestamps.peek() > self._ma_length_in_seconds:
                self._timestamps.dequeue()
                removing_from_ma = self._numbers_in_sum.dequeue()
                self._sum_of_data -= removing_from_ma
        
        #Add new data point
        self._sum_of_data += value
        self._numbers_in_sum.enqueue(value)
        self._timestamps.enqueue(timestamp)
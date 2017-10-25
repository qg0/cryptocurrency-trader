'''
Parent object of all other Strategies.
Enables observers to be notified when an action should take place.

@author Tobias Carryer
'''

class Strategy(object):
    
    def __init__(self):
        self.observers = []
        
    def attach_observer(self, observer):
        '''
        Post: Observer will be notified when the strategy says to buy or sell.
        Throws: ValueError if observer is None
        '''
        
        if observer == None:
            raise ValueError("observer cannot be None")
        self.observers.append(observer)
        
    def notify_observers(self, should_buy, market_value):
        for observer in self.observers:
            observer.notify_significant_change(should_buy, market_value)
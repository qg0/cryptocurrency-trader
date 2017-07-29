'''
Makes buying and selling decisions.

@author: Tobias Carryer
'''

from abc import ABCMeta, abstractmethod

class Trader(object):
    
    __metaclass__ = ABCMeta
    
    def __init__(self, is_test, minimum_trade):
        print("Created a trader.")
        self.balance = None
        self.assets = None
        self.can_buy = True
        self.is_test = is_test
        self.minimum_trade = minimum_trade
        
        #Threshold above which a valuation is not considered valid.
        self.outlier_threshold = 5000
    
    @abstractmethod
    def buy(self, market_value):
        '''
        Post: get_balance() is lower by percent_to_spend
        '''
        
        print("buy is expected to be overriden by a child of Trader")
        
    @abstractmethod
    def sell(self, market_value):
        '''
        Post: get_assets() is lower by percent_to_sell
        '''
        
        print("sell is expected to be overriden by a child of Trader")
        
    @abstractmethod
    def fetch_balance(self):
        print("fetch_balance is expected to be overriden by a child of Trader")
        raise NotImplementedError
    
    @abstractmethod
    def fetch_assets(self):
        print("fetch_assets is expected to be overriden by a child of Trader")
        raise NotImplementedError
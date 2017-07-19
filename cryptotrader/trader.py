'''
Makes buying and selling decisions.

@author: Tobias Carryer
'''

from abc import ABCMeta, abstractmethod

class Trader(object):
    
    __metaclass__ = ABCMeta
    
    def __init__(self, is_test):
        print("Created a trader.")
        self.balance = None
        self.assets = None
        self.can_buy = True
        self.sell_all_assets = False
        self.is_test = is_test
        
        #When the market changes significantly this is how much to buy or sell
        self.percent_to_spend_on_buy = 0.20
        self.percent_of_assets_to_sell = 1.00
        
        #Threshold above which a valuation is not considered valid.
        self.outlier_threshold = 5000
    
    @abstractmethod
    def buy(self, percent_to_spend, market_value):
        '''
        Post: get_balance() is lower by percent_to_spend
        '''
        
        print("buy is expected to be overriden by a child of Trader")
        
    @abstractmethod
    def sell(self, percent_to_sell, market_value):
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
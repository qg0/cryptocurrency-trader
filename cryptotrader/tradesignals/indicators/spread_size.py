'''
Indicates when the spread is big enough to be profitable.
@author Tobias Carryer
'''

from decimal import Decimal, localcontext

class SpreadSize(object):
    
    def __init__(self, minimum_return=1.005, market_fee=0.005):
        '''
        Pre: minimum_return is a positive percentage. It has to be greater than 1 or the indicator
             will give bad signals.
             market_fee is a percentage.
        '''
        self.minimum_return = Decimal(minimum_return)
        self.keep_after_fee_squared = Decimal((1 - market_fee) * (1 - market_fee))
        
    def is_profitable(self, highest_bid, lowest_ask):
        '''
        Returns: True if the spread is profitable, False if it is not.
        '''
        
        with localcontext() as context:
            context.prec = 8
        
            spread = Decimal(lowest_ask - highest_bid)
            
            return spread > self.minimum_return * highest_bid / self.keep_after_fee_squared - highest_bid
        
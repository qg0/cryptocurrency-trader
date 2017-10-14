class QuadrigaOptions(object):
    '''
    Class to hold options that are passed to the trader and pipeline.
    Makes it easier to switch between markets by only changing the ticker in one place in the code.
    '''
    
    # In each entry: index 0 is the major currency, index 1 is the minor currency.
    _pairs = {"eth_cad": ["eth", "cad"], "btc_cad": ["btc", "cad"], "ltc_cad": ["ltc", "cad"],
                 "btc_usd": ["btc", "usd"], "eth_btc": ["eth", "btc"]}
    
    # Note: ETH_CAD minimum is actually $1.00 CAD but is represented as assets (ETH) to be consistent.
    _minimum_trades = {"eth_cad": 0.01, "btc_cad": 0.0005, "ltc_cad": 0.0001,
                 "btc_usd": 0.005, "eth_btc": 0.000001}
    
    _undercut_by = {"eth_cad": 0.01, "btc_cad": 0.01, "ltc_cad": 0.01,
                 "btc_usd": 0.01, "eth_btc": 0.0000005}
    
    # Number of decimal places in prices.
    _amount_precision = {"eth_cad": 8, "btc_cad": 8, "ltc_cad": 8, "btc_usd": 8, "eth_btc": 8}
    _price_precision = {"eth_cad": 2, "btc_cad": 2, "ltc_cad": 2, "btc_usd": 2, "eth_btc": 8}
    
    def __init__(self, ticker):
        '''
        Pre: ticker must be from QuadrigaTickers
        Post: This object has set ticker, major_currency, minor_currency, minimum_trade, and undercut.
              minimum_trade is the minimum amount of assets that can be sold on a trade.
              undercut is the amount of bid/ask higher/lower than other orders.
        '''
        
        self.ticker = ticker
        self.major_currency = QuadrigaOptions._pairs[ticker][0]
        self.minor_currency = QuadrigaOptions._pairs[ticker][1]
        self.minimum_trade = QuadrigaOptions._minimum_trades[ticker]
        self.undercut = QuadrigaOptions._undercut_by[ticker]
        self.amount_precision = QuadrigaOptions._amount_precision[ticker]
        self.price_precision = QuadrigaOptions._price_precision[ticker]
        
class QuadrigaTickers:
    # Prevents magic strings and makes it easy to tell what markets are available.
    # These tickers can be used in API URLs.
    ETH_CAD = "eth_cad"
    BTC_CAD = "btc_cad"
    LTC_CAD = "ltc_cad"
    BTC_USD = "btc_usd"
    ETH_BTC = "eth_btc"
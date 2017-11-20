'''
Fetch trading signals from investing.com

@author: Tobias Carryer
'''

import requests
from bs4 import BeautifulSoup
from decimal import Decimal
from cryptotrader.tradesignals.strategies import Strategy
from cryptotrader.bittrex.bittrex_options import bittrex_btc_undercut

class InvestingDotComStrategy(Strategy):
    
    def __init__(self, market_url, undercut=bittrex_btc_undercut):
        '''
        URLs can be obtained from https://www.investing.com/crypto/currencies
        Make sure the right market is selected before passing the URL to the strategy.
        '''
        Strategy.__init__(self)
        self.market_url = market_url
        self.undercut = undercut
        
    def get_trading_signal(self, to_bid, to_ask):
        '''
        to_bid and to_ask are the values to bid/ask depending on the signal generated.
        '''
        signal = self.get_trading_signal_from(fetch_website(self.market_url))
        if signal == True:
            self.notify_observers(signal, Decimal(to_bid)+self.undercut)
        elif signal == False:
            self.notify_observers(signal, Decimal(to_ask)-self.undercut)
        else: #Holding, market value to buy/sell at is irrelevant
            self.notify_observers(signal, -1)
            
    def get_trading_signal_from(self, website_html):
        soup = BeautifulSoup(website_html, "lxml")
        
        # Get the table that summarize the trading signals.
        table = soup.find('table', {'class':'technicalSummaryTbl'})
        
        # The last row in the table is the summary row.
        trs = table.findChildren("tr")
        tds = trs[len(trs)-1].findChildren("td")
        
        # Assert that the summary row was loaded.
        # Crashing early prevents any trades executing based on a broken strategy.
        if tds[0].text != "Summary":
            raise RuntimeWarning("First column in the summary row should read 'Summary'. Instead, it contained: "  + tds[0].text)
        
        # Buy/sell if the 5 minute and 15 minute signals both agree on a strong trend
        # Hold by default
        should_buy = None
        if tds[1].text == "Strong Buy" and tds[2].text == "Strong Buy":
            should_buy = True
        elif tds[1].text == "Strong Sell" and tds[2].text == "Strong Sell":
            should_buy = False
        return should_buy
            
def fetch_website(url):
    # Spoof a human client
    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}
    response = requests.get(url, headers=hdr)
    return response.content
    
if __name__ == "__main__":
    print fetch_website("https://www.investing.com/currencies/xrp-btc?cid=1031049")
        
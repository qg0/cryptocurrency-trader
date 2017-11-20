import requests
from decimal import Decimal, localcontext

def satoshi_to_usd( satoshi ):
    '''
    Pre: satoshi is a Decimal.
    Returns: A Decimal with eight significant decimal places. The value of the satoshi in USD.
    '''
    with localcontext() as context:
        context.prec = 8
        return satoshi * current_price_of_bitcoin()
    
    
def current_price_of_bitcoin():
    '''
    Pre: coinmarketcap's api can be accessed. This will require an internet connection.
    Returns: The price of Bitcoin in USD according to coinmarketcap.com
             The variable will be a Decimal with eight decimal places.
    '''
    with localcontext() as context:
        context.prec = 8
        r = requests.get("https://api.coinmarketcap.com/v1/ticker/bitcoin/")
        return Decimal(r.json()[0]["price_usd"])
    
if __name__ == "__main__":
    # Test converting satoshis to USD
    print "0.00000001 satoshi = " + str(satoshi_to_usd(Decimal(0.00000001))) + " USD"
    print "0.00000002 satoshi = " + str(satoshi_to_usd(Decimal(0.00000002))) + " USD"
    print "0.00000003 satoshi = " + str(satoshi_to_usd(Decimal(0.00000003))) + " USD"
    print "0.00000010 satoshi = " + str(satoshi_to_usd(Decimal(0.00000010))) + " USD"
    print "0.00000025 satoshi = " + str(satoshi_to_usd(Decimal(0.00000025))) + " USD"
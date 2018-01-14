import requests
from decimal import Decimal

def get_coinmarketcap_price(coinmarketcap_id):
    '''
    coinmarketcap_id is the coin's full name in lower case. Spaces are replaced with -
    :returns: the coin's price in BTC
    '''
    coin_info = requests.get("https://api.coinmarketcap.com/v1/ticker/"+coinmarketcap_id+"/").json()
    return Decimal(coin_info[0]["price_btc"])
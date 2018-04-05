from decimal import Decimal

def sum_liquidity(book, max_price=None, min_price=None):
    '''
    max_price is for summing sells
    min_price is for summing buys
    Assumes the format [{"Price": number, "Quantity": number}]
    '''
    sum_of_orders = Decimal(0)
    for entry in book:
        if max_price:
            if Decimal(entry["Price"]) > max_price:
                sum_of_orders += Decimal(entry["Quantity"])
            else:
                break
        else:
            if entry["Price"] < min_price:
                sum_of_orders += Decimal(entry["Quantity"])
            else:
                break
    return sum_of_orders
                
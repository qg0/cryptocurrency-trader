from decimal import Decimal
from math import floor
def quantity_adjusted_for_decimals(quantity):
    return Decimal(floor(quantity * Decimal(100000000))) / Decimal(100000000)
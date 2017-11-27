from decimal import Decimal
cryptopia_fee = Decimal(0.002) # Fee is a percentage
minimum_trade_for = {"BTC": Decimal(0.00005000),
                     "LTC": Decimal(0.00100000),
                     "USDT": Decimal(0.20000000),
                     "NZDT": Decimal(0.20000000),
                     "DOGE": Decimal(1.00000000)}
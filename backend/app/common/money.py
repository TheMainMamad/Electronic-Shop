from decimal import Decimal
from typing import Annotated

from pydantic import PlainSerializer

# NUMERIC(x, 0) columns hold whole toman amounts, but Decimal arithmetic
# (e.g. unit_price * quantity) can produce a result whose internal exponent
# renders as scientific notation ("5.000E+7") when serialized — which would
# show up broken in the storefront. Force plain fixed-point notation instead.
Money = Annotated[Decimal, PlainSerializer(lambda v: format(v, "f"), return_type=str)]

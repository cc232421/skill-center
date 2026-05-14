import sys
from unittest.mock import MagicMock

_m = MagicMock()
_m.MACD.return_value = (None, None, None)
_m.BBANDS.return_value = (None, None, None)
sys.modules['talib'] = _m

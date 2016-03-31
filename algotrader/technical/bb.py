import datetime

import numpy as np

from algotrader.technical import Indicator
from algotrader.utils.time_series import TimeSeries
from algotrader.technical.ma import SMA
from algotrader.technical.stats import STD
import math

class BB(Indicator):
    _slots__ = (
        'length',
        'num_std'
        '__sma',
        'upper',
        'lower',
        '__std_dev',
    )

    @classmethod
    def get_name(cls, input, length, num_std):
        name = input.name if isinstance(input, TimeSeries) else input
        return "BB(%s,%s,%s)" % (name, length, num_std)

    def __init__(self, input, length=14, num_std = 3, description="Bollinger Bands"):
        super(BB, self).__init__(BB.get_name(input, length, num_std), input, description)
        self.length = length
        self.num_std = num_std
        self.__sma = SMA(input, length)
        self.__std_dev = STD(input, length)
        self.upper = TimeSeries("BBU(%s, %s)" % (input.name, length))
        self.lower = TimeSeries("BBL(%s, %s)" % (input.name, length))

    def on_update(self, time_value):
        time, value = time_value
        sma = self.__sma.now()
        std = self.__std_dev.now()
        if not np.isnan(sma):
            upper = sma + std * self.num_std
            lower = sma - std * self.num_std
            self.upper.add(time, upper)
            self.lower.add(time, lower)
            self.add(time, sma)
        else:
            self.upper.add(time, np.nan)
            self.lower.add(time, np.nan)
            self.add(time, np.nan)




from algotrader.event.order import OrdAction
from algotrader.strategy.strategy import Strategy
from algotrader.tools import logger


class Down2PctStrategy(Strategy):
    def __init__(self, stg_id, broker_id, feed, portfolio, qty=1000):
        super(Down2PctStrategy, self).__init__(stg_id, broker_id, feed, portfolio)
        self.__prev_bar = None
        self.__curr_bar = None
        self.day_count = 0
        self.order = None
        self.qty = 1000

    def on_bar(self, bar):
        self.__prev_bar = self.__curr_bar
        self.__curr_bar = bar

        if self.order is None:
            roc = self.roc()
            if roc < -0.02:
                logger.info("[%s] buying....date = %s, roc = %s" % (self.__class__.__name__, bar.timestamp, roc))
                self.order = self.new_market_order(instrument=bar.instrument, action=OrdAction.BUY, qty=self.qty)
                self.day_count = 0
        else:
            self.day_count += 1
            if self.day_count >= 5:
                logger.info("[%s] selling....date = %s, day_count = %s" % (self.__class__.__name__,bar.timestamp, self.day_count))
                self.new_market_order(instrument=bar.instrument, action=OrdAction.SELL, qty=self.qty)
                self.order = None

    def roc(self):
        if self.__curr_bar and self.__prev_bar:
            return (self.__curr_bar.close_or_adj_close() - self.__prev_bar.close_or_adj_close()) / self.__prev_bar.close_or_adj_close()
        return 0
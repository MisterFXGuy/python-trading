from algotrader.event.event_bus import EventBus
from algotrader.event.order import *
from algotrader.provider import *
from algotrader.tools import *


class Broker(Provider, OrderEventHandler):
    __metaclass__ = abc.ABCMeta

    def start(self):
        pass


@singleton
class Simulator(Broker, MarketDataEventHandler):
    ID = "Simulator"

    def start(self):
        EventBus.data_subject.subscribe(self.on_next)

    def stop(self):
        pass

    def on_bar(self, bar):
        logger.debug("[%s] %s" % (self.__class__.__name__, bar))

    def on_quote(self, quote):
        logger.debug("[%s] %s" % (self.__class__.__name__, quote))

    def on_trade(self, trade):
        logger.debug("[%s] %s" % (self.__class__.__name__, trade))

    def on_order(self, order):
        logger.debug("[%s] %s" % (self.__class__.__name__, order))


broker_mapping = {
    Simulator.ID: Simulator()
}


def get_broker(broker_id):
    return broker_mapping[broker_id]

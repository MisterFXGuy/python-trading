from collections import defaultdict

from algotrader.event.event_bus import EventBus
from algotrader.event.market_data import MarketDataEventHandler
from algotrader.event.order import OrdStatus, OrderStatusUpdate, \
    ExecutionReport
from algotrader.provider.broker.sim.commission import NoCommission
from algotrader.provider.broker.sim.fill_strategy import DefaultFillStrategy
from algotrader.provider.provider import broker_mgr, Broker
from algotrader.trading.order_mgr import order_mgr
from algotrader.utils import clock
from algotrader.utils import logger


class Simulator(Broker, MarketDataEventHandler):
    ID = "Simulator"

    def __init__(self, exec_handler=order_mgr, commission=None, fill_strategy=None):

        super(Simulator, self).__init__()
        self.__next_exec_id = 0
        self.__ord_req_map = defaultdict(dict)
        self.__ord_req_fill_status = {}
        self.__quote_map = {}
        self.__exec_handler = exec_handler
        self.__fill_strategy = fill_strategy if fill_strategy is not None else DefaultFillStrategy()
        self.__commission = commission if commission is not None else NoCommission()

        broker_mgr.register(self)

    def start(self):
        EventBus.data_subject.subscribe(self.on_next)

    def stop(self):
        pass

    def id(self):
        return Simulator.ID

    def next_exec_id(self):
        __next_exec_id = self.__next_exec_id
        self.__next_exec_id += 1
        return __next_exec_id

    def on_bar(self, bar):
        self.__process_event(bar)

    def on_quote(self, quote):
        self.__process_event(quote)

    def on_trade(self, trade):
        self.__process_event(trade)

    def __process_event(self, event):
        logger.debug("[%s] %s" % (self.__class__.__name__, event))
        if event.inst_id in self.__ord_req_map:
            for new_ord_req in self.__ord_req_map[event.inst_id].values():
                fill_info = self.__fill_strategy.process_w_market_data(new_ord_req, event, False)
                executed = self.execute(new_ord_req, fill_info)

    def on_new_ord_req(self, new_ord_req):
        logger.debug("[%s] %s" % (self.__class__.__name__, new_ord_req))

        self.__add_order(new_ord_req)
        self.__send_exec_report(new_ord_req, 0, 0, OrdStatus.SUBMITTED)

        fill_info = self.__fill_strategy.process_new_order(new_ord_req)
        executed = self.execute(new_ord_req, fill_info)

    def __add_order(self, new_ord_req):
        ord_reqs = self.__ord_req_map[new_ord_req.inst_id]
        ord_reqs[new_ord_req.ord_id] = new_ord_req

    def __remove_order(self, new_ord_req):
        if new_ord_req.inst_id in self.__ord_req_map:
            ord_reqs = self.__ord_req_map[new_ord_req.inst_id]
            if new_ord_req.ord_id in ord_reqs:
                del ord_reqs[new_ord_req.ord_id]

    def execute(self, new_ord_req, fill_info):
        if not fill_info or fill_info.fill_price <= 0 or fill_info.fill_price <= 0:
            return False

        # new_ord_req is removed
        if new_ord_req.inst_id not in self.__ord_req_map:
            return False

        total_filled_qty = self.__ord_req_fill_status.get(new_ord_req.ord_id, 0)
        price = fill_info.fill_price
        qty = fill_info.fill_qty
        leave_qty = new_ord_req.qty - total_filled_qty

        if qty < leave_qty:
            total_filled_qty += qty
            self.__ord_req_fill_status[new_ord_req.ord_id]=total_filled_qty

            self.__send_exec_report(new_ord_req, price, qty, OrdStatus.PARTIALLY_FILLED)
            return False
        else:
            qty = leave_qty
            total_filled_qty += qty
            self.__ord_req_fill_status[new_ord_req.ord_id]=total_filled_qty

            self.__send_exec_report(new_ord_req, price, qty, OrdStatus.FILLED)
            self.__remove_order(new_ord_req)
            return True

    def __send_status(self, new_ord_req, ord_status):
        ord_update = OrderStatusUpdate(broker_id=Simulator.ID,
                                       ord_id=new_ord_req.ord_id,
                                       inst_id=new_ord_req.inst_id,
                                       timestamp=clock.default_clock.current_date_time(),
                                       status=ord_status)
        self.__exec_handler.on_ord_upd(ord_update)

    def __send_exec_report(self, new_ord_req, last_price, last_qty, ord_status):
        commission = self.__commission.calc(new_ord_req, last_price, last_qty)
        exec_report = ExecutionReport(broker_id=Simulator.ID,
                                      ord_id=new_ord_req.ord_id,
                                      inst_id=new_ord_req.inst_id,
                                      timestamp=clock.default_clock.current_date_time(),
                                      er_id=self.next_exec_id(),
                                      last_qty=last_qty,
                                      last_price=last_price,
                                      status=ord_status,
                                      commission=commission)

        self.__exec_handler.on_exec_report(exec_report)

    def _get_orders(self):
        return self.__ord_req_map


simulator = Simulator();

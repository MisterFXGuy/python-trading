from unittest import TestCase

from algotrader.event.market_data import Bar
from algotrader.event.order import ExecutionEventHandler, NewOrderSingle, OrdStatus, OrdAction, OrdType
from algotrader.provider.broker.sim.simulator import Simulator
from algotrader.trading.instrument_data import inst_data_mgr


class SimulatorTest(TestCase):
    class ExecHandler(ExecutionEventHandler):
        def __init__(self):
            self.ord_upds = list()
            self.exec_reports = list()

        def on_ord_upd(self, ord_upd):
            self.ord_upds.append(ord_upd)

        def on_exec_report(self, exec_report):
            self.exec_reports.append(exec_report)

        def reset(self):
            self.ord_upds = list()
            self.exec_reports = list()

    def setUp(self):
        inst_data_mgr.clear()

        self.exec_handler = SimulatorTest.ExecHandler()
        self.simulator = Simulator(exec_handler=self.exec_handler)

    def test_on_limit_order_fill_with_new_data(self):
        orders = self.simulator._get_orders()
        self.assertEqual(0, len(orders))

        order1 = NewOrderSingle(ord_id=1, inst_id=1, action=OrdAction.BUY, type=OrdType.LIMIT, qty=1000, limit_price=18.5)
        self.simulator.on_new_ord_req(order1)

        orders = self.simulator._get_orders()
        self.assertEqual(1, len(orders))
        self.assertTrue(order1.inst_id in orders)
        self.assertEqual(1, len(orders[order1.inst_id]))
        self.assertTrue(order1.ord_id in orders[order1.inst_id])
        self.assertEqual(1, len(self.exec_handler.exec_reports))

        exec_report = self.exec_handler.exec_reports[0]
        self.assert_exec_report(exec_report, order1.ord_id, 0, 0, OrdStatus.SUBMITTED)

        bar1 = Bar(inst_id=1, open=20, high=21, low=19, close=20.5, vol=1000)
        bar2 = Bar(inst_id=1, open=16, high=18, low=15, close=17, vol=1000)

        self.exec_handler.reset()
        self.simulator.on_bar(bar1)
        self.assertEqual(0, len(self.exec_handler.exec_reports))

        self.exec_handler.reset()
        self.simulator.on_bar(bar2)
        self.assertEqual(1, len(self.exec_handler.exec_reports))
        exec_report = self.exec_handler.exec_reports[0]
        self.assert_exec_report(exec_report, order1.ord_id, 1000, 18.5, OrdStatus.FILLED)

    def test_on_limit_order_immediate_fill(self):
        bar1 = Bar(inst_id=1, open=20, high=21, low=19, close=20.5, vol=1000)
        bar2 = Bar(inst_id=1, open=16, high=18, low=15, close=17, vol=1000)

        inst_data_mgr.on_bar(bar2)

        orders = self.simulator._get_orders()
        self.assertEqual(0, len(orders))

        order1 = NewOrderSingle(ord_id=1, inst_id=1, action=OrdAction.BUY, type=OrdType.LIMIT, qty=1000, limit_price=18.5)
        self.simulator.on_new_ord_req(order1)

        orders = self.simulator._get_orders()
        self.assertEqual(1, len(orders))
        self.assertTrue(order1.inst_id in orders)
        self.assertEqual(0, len(orders[order1.inst_id]))

        self.assertEqual(2, len(self.exec_handler.exec_reports))

        exec_report = self.exec_handler.exec_reports[0]
        self.assert_exec_report(exec_report, order1.ord_id, 0, 0, OrdStatus.SUBMITTED)

        exec_report = self.exec_handler.exec_reports[1]
        self.assert_exec_report(exec_report, order1.ord_id, 1000, 18.5, OrdStatus.FILLED)

    def assert_exec_report(self, exec_report, ord_id, last_qty, last_price, status):
        self.assertEqual(ord_id, exec_report.ord_id)
        self.assertEqual(last_qty, exec_report.last_qty)
        self.assertEqual(last_price, exec_report.last_price)
        self.assertEqual(status, exec_report.status)

#-*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#   Prestashoperpconnect for OpenERP                                          #
#   Copyright (C) 2013 Akretion                                               #
#                                                                             #
#   This program is free software: you can redistribute it and/or modify      #
#   it under the terms of the GNU Affero General Public License as            #
#   published by the Free Software Foundation, either version 3 of the        #
#   License, or (at your option) any later version.                           #
#                                                                             #
#   This program is distributed in the hope that it will be useful,           #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#   GNU Affero General Public License for more details.                       #
#                                                                             #
#   You should have received a copy of the GNU Affero General Public License  #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################
from prestapyt import PrestaShopWebServiceDict

from openerp.osv import fields, orm
import openerp.addons.decimal_precision as dp
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.event import on_record_write
from openerp.addons.connector.unit.synchronizer import (Exporter)
from .unit.backend_adapter import GenericAdapter

from openerp.addons.connector_ecommerce.unit.sale_order_onchange import (
    SaleOrderOnChange)
from .connector import get_environment
from backend import prestashop


@prestashop
class PrestaShopSaleOrderOnChange(SaleOrderOnChange):
    _model_name = 'prestashop.sale.order'


@prestashop
class SaleOrderStateAdapter(GenericAdapter):
    _model_name = 'prestashop.sale.order.state'
    _prestashop_model = 'order_states'


@prestashop
class SaleOrderAdapter(GenericAdapter):
    _model_name = 'prestashop.sale.order'
    _prestashop_model = 'orders'
    _export_node_name = 'order'

    def update_sale_state(self, prestashop_id, datas):
        api = self.connect()
        return api.add('order_histories', datas)

    def search(self, filters=None):
        result = super(SaleOrderAdapter, self).search(filters=filters)

        shops = self.session.env['prestashop.shop'].search([
            ('backend_id', '=', self.backend_record.id)
        ])
        for shop in shops:
            if not shop.default_url:
                continue

            api = PrestaShopWebServiceDict(
                '%s/api' % shop.default_url, self.prestashop.webservice_key
            )
            result += api.search(self._prestashop_model, filters)
        return result


@prestashop
class OrderCarriers(GenericAdapter):
    _model_name = '__not_exit_prestashop.order_carrier'
    _prestashop_model = 'order_carriers'
    _export_node_name = 'order_carrier'


@prestashop
class PaymentMethodAdapter(GenericAdapter):
    _model_name = 'payment.method'
    _prestashop_model = 'orders'
    _export_node_name = 'order'

    def search(self, filters=None):
        api = self.connect()
        res = api.get(self._prestashop_model, options=filters)
        methods = res[self._prestashop_model][self._export_node_name]
        if isinstance(methods, dict):
            return [methods]
        return methods


@prestashop
class SaleOrderLineAdapter(GenericAdapter):
    _model_name = 'prestashop.sale.order.line'
    _prestashop_model = 'order_details'


@prestashop
class SaleStateExporter(Exporter):
    _model_name = ['prestashop.sale.order']

    def run(self, prestashop_id, state):
        datas = {
            'order_history': {
                'id_order': prestashop_id,
                'id_order_state': state,
            }
        }
        self.backend_adapter.update_sale_state(prestashop_id, datas)


# TODO improve me, make the search on the sale order backend only
@on_record_write(model_names='sale.order')
def prestashop_sale_state_modified(session, model_name, record_id, vals):
    if 'state' in vals:
        sale = session.env[model_name].browse(record_id)
        if not sale.prestashop_bind_ids:
            return True
        # a quick test to see if it is worth trying to export sale state
        states = session.env['sale.order.state.list'].search(
            [('name', '=', sale.state)]
        )
        if states:
            export_sale_state.delay(session, model_name, record_id, priority=20)
    return True


def find_prestashop_state(session, sale_state, backend_id):
    state_list_model = session.env['sale.order.state.list']
    for state_list in state_list_model.search([('name', '=', sale_state)]):
        if state_list.prestashop_state_id.backend_id.id == backend_id:
            return state_list.prestashop_state_id.prestashop_id
    return None


@job
def export_sale_state(session, model_name, record_id):
    binding_model = session.env['prestashop.sale.order']
    for sale in binding_model.search([('openerp_id', '=', record_id)]):
        backend_id = sale.backend_id.id
        new_state = find_prestashop_state(session, sale.state, backend_id)
        if new_state is None:
            continue
        env = get_environment(session, 'prestashop.sale.order', backend_id)
        sale_exporter = env.get_connector_unit(SaleStateExporter)
        sale_exporter.run(sale.prestashop_id, new_state)

# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Florian da Costa
#    Copyright 2015 Akretion
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp.tools.translate import _
from openerp.addons.connector.exception import FailedJobError
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.mapper import (mapping,
                                                  only_create
                                                  )
from openerp.addons.connector_ecommerce.event import on_product_price_changed
from openerp.addons.prestashoperpconnect.product import (
    ProductMapper,
    ProductAdapter)
from openerp.addons.prestashoperpconnect.unit.export_synchronizer import (
    ExportSynchronizer)
from openerp.addons.prestashoperpconnect.connector import get_environment
from openerp.addons.prestashoperpconnect.backend import prestashop
#from .product_combination import export_combination_price
from openerp.addons.connector.unit.backend_adapter import BackendAdapter
import requests


# TODO: replace a price mapper only, not the full mapper
@prestashop(replacing=ProductMapper)
class ProductMapper(ProductMapper):
    _model_name = 'prestashop.product.product'

    @only_create
    @mapping
    def price(self, record):
        """ The price is imported at the creation of
        the product, then it is only modified and exported
        from OpenERP """
        return super(ProductMapper, self).price(record)

@prestashop
class ProductPriceExporter(ExportSynchronizer):
    """ Export the price of a product.

    Use the pricelist configured on the backend for the
    default price in Prestashop.
    """
    _model_name = ['prestashop.product.product']

    def get_datas(self, binding):
        datas = {}
        pricelist_id = binding.backend_id.pricelist_id.id
        new_price = self._get_price(pricelist_id)
        print new_price
        datas['pricewithouttax'] = new_price
        datas['id_product'] = binding.prestashop_id
        datas['key'] = binding.backend_id.webservice_key
        return datas

    def _get_price(self, pricelist_id):
        """ Return the raw OpenERP data for ``self.binding_id`` """
        if pricelist_id is None:
            return False
        with self.session.change_context({'pricelist': pricelist_id}):
            return self.session.read(self.model._name,
                                    self.binding_id,
                                    ['list_price'])['list_price']

    def update_price(self, url, datas):
        req = requests.post(url, data=datas)
        return req.text


    def run(self, record_id):
        self.binding_id = record_id
        product = self.session.browse(self.model._name, record_id)
        datas = self.get_datas(product)
        url = product.backend_id.location + '/updateprice.php'
        print url, 'kk', datas
        res = self.update_price(url, datas)
        return True

@on_product_price_changed
def product_price_changed(session, model_name, record_id, fields=None):
    """ When a product.product price has been changed """
    if session.context.get('connector_no_export'):
        return
    model = session.pool.get(model_name)
    record = model.browse(session.cr, session.uid,
                          record_id, context=session.context)
    if not record.sale_ok:
        return
    for binding in record.prestashop_bind_ids:
        export_product_price.delay(session,
                                   binding._model._name,
                                   binding.id)
    for binding in record.prestashop_combinations_bind_ids:
        export_product_price.delay(session,
                                   binding._model._name,
                                   binding.id)


@job
def export_product_price(session, model_name, record_id):
    """ Export the price of a product. """
    product_bind = session.browse(model_name, record_id)
    backend_id = product_bind.backend_id.id
    env = get_environment(session, model_name, backend_id)
    price_exporter = env.get_connector_unit(ProductPriceExporter)
    return price_exporter.run(record_id)

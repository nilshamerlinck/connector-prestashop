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
from openerp.addons.prestashoperpconnect.product_combination import (
    ProductCombinationMapper)
from openerp.addons.prestashoperpconnect.unit.export_synchronizer import (
    ExportSynchronizer)
from openerp.addons.prestashoperpconnect.connector import get_environment
from openerp.addons.prestashoperpconnect.backend import prestashop
from .product import ProductPriceExporter


# TODO: replace a price mapper only, not the full mapper
@prestashop(replacing=ProductCombinationMapper)
class ProductCombinationMapper(ProductCombinationMapper):
    _model_name = 'prestashop.product.combination'

    @only_create
    @mapping
    def price(self, record):
        """ The price is imported at the creation of
        the product, then it is only modified and exported
        from OpenERP """
        return super(ProductCombinationMapper, self).price(record)



@prestashop
class CombinationPriceExporter(ProductPriceExporter):
    """ Export the price of a product.

    Use the pricelist configured on the backend for the
    default price in Prestashop.
    """
    _model_name = ['prestashop.product.combination']

    def get_datas(self, binding):
        datas = {}
        pricelist_id = binding.backend_id.pricelist_id.id
        combination_price = self._get_price(pricelist_id)
        datas['pricecombinationwithouttax'] = combination_price
        datas['id_combination'] = binding.prestashop_id
        datas['key'] = binding.backend_id.webservice_key
        return datas


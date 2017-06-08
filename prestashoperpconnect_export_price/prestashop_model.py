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

from openerp.osv import fields, orm
from openerp.tools.translate import _
from openerp.addons.connector.session import ConnectorSession
from .product import export_product_price


class PrestashopBackend(orm.Model):
    _inherit = 'prestashop.backend'

    def _get_pricelist_id(self, cr, uid, context=None):
        data_obj = self.pool.get('ir.model.data')
        ref = data_obj.get_object_reference(cr, uid, 'product', 'list0')
        if ref:
            return ref[1]
        return False

    _columns = {
        'pricelist_id': fields.many2one('product.pricelist',
                                        'Pricelist',
                                        required=True,
                                        domain="[('type', '=', 'sale')]",
                                        help='The price list used to define '
                                             'the prices of the products in '
                                             'Magento.'),
    }

    _defaults = {
        'pricelist_id': _get_pricelist_id,
    }

    def onchange_pricelist_id(self, cr, uid, ids, pricelist_id, context=None):
        if not ids:  # new record
            return {}
        warning = {
            'title': _('Warning'),
            'message': _('If you change the pricelist of the backend, '
                         'the price of all the products will be updated '
                         'in Prestashop.')
        }
        return {'warning': warning}

    def update_all_prices(self, cr, uid, ids, context=None):
        """ Update the prices of all the products linked to the
        backend. """
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        for backend in self.browse(cr, uid, ids, context=context):
            session = ConnectorSession(cr, uid, context=context)
            product_binding_ids = session.search(
                'prestashop.product.product',
                [('backend_id', '=', backend.id), ('sale_ok', '=', True)])
            combination_binding_ids = session.search(
                'prestashop.product.combination',
                [('backend_id', '=', backend.id)])
            for product_bind_id in product_binding_ids:
                export_product_price.delay(session,
                                           'prestashop.product.product',
                                           product_bind_id)
            for combination_bind_id in combination_binding_ids:
                export_product_price.delay(session,
                                           'prestashop.product.combination',
                                           combination_bind_id)
        return True

    def write(self, cr, uid, ids, vals, context=None):
        if 'pricelist_id' in vals:
            self.update_all_prices(cr, uid, ids, context=context)
        return super(PrestashopBackend, self).write(cr, uid, ids,
                                                  vals, context=context)


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


from openerp.osv import orm

class PrestashopProductProduct(orm.Model):
    _inherit = 'prestashop.product.product'

    def _prestashop_qty(self, cr, uid, product, context=None):
        return product.bom_stock


class PrestashopProductCombination(orm.Model):
    _inherit = 'prestashop.product.combination'

    def _prestashop_qty(self, cr, uid, product, context=None):
        return product.bom_stock


class product_product(orm.Model):
    _inherit = 'product.product'

    def update_prestashop_quantities(self, cr, uid, ids, context=None):
        super(product_product, self).update_prestashop_quantities(
            cr, uid, ids, context=context)
        bom_obj = self.pool['mrp.bom']
        for product in self.browse(cr, uid, ids, context=context):
            bom_ids = bom_obj.search(cr, uid,
                [('product_id', '=', product.id)])
            for bom in bom_obj.browse(cr, uid, bom_ids, context=context):
                if bom.bom_id:
                    context
                    prod_id = bom.bom_id.product_id.id
                    self.update_prestashop_quantities(cr, uid, [prod_id],
                                                      context=context)
        return True

            




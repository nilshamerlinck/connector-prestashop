# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component


class ProductImageDelete(Component):
    _name = 'prestashop.product.image.deleter'
    _inherit = 'prestashop.deleter'
    _apply_on = 'prestashop.product.image'

    _model_name = 'prestashop.product.image'

    def run(self, external_id, product_id):
        self.backend_adapter.delete(external_id, product_id)
        return ('Image %s of the product %s deleted on Prestashop') % (external_id, product_id)

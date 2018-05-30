# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields
from odoo.addons.connector.components.mapper import mapping, changed_by
from odoo.addons.component.core import Component


class PrestashopProductTemplate(models.Model):
    _inherit = 'prestashop.product.template'

    default_categ_id = fields.Many2one(comodel_name='product.category',
                                       string='Default category')


class ProductTemplateCategoryExportMapper(Component):
    _inherit = 'prestashop.product.template.export.mapper'

    @changed_by('default_categ_id')
    @mapping
    def default_categ_id(self, record):
        binder = self.binder_for('prestashop.product.category')
        ext_id = binder.to_external(record.default_categ_id.id, wrap=True)
        if ext_id:
            return {'id_category_default': ext_id}
        return {}

    def _get_product_category(self, record):
        """
        Don't use the main categ but the default categ.
        """
        ext_categ_ids = []
        binder = self.binder_for('prestashop.product.category')
        categories = list(set(record.categ_ids + record.default_categ_id))
        for category in categories:
            ext_id = binder.to_external(category.id, wrap=True)
            if ext_id:
                ext_categ_ids.append({'id': ext_id})
        return ext_categ_ids

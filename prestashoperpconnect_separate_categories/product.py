# -*- coding: utf-8 -*-
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

from openerp import models, fields
from openerp.addons.prestashoperpconnect.backend import prestashop
from openerp.addons.connector.unit.mapper import changed_by, mapping
from openerp.addons.prestashoperpconnect_catalog_manager.product import ProductTemplateExportMapper


class PrestashopProductTemplate(models.Model):
    _inherit = 'prestashop.product.template'

    default_categ_id = fields.Many2one(comodel_name='product.category',
                                       string='Default category')


@prestashop(replacing=ProductTemplateExportMapper)
class ProductTemplateCategoryExportMapper(ProductTemplateExportMapper):
    _model_name = 'prestashop.product.template'

    @changed_by('default_categ_id')
    @mapping
    def default_categ_id(self, record):
        binder = self.binder_for('prestashop.product.category')
        ext_id = binder.to_backend(record.default_categ_id.id, wrap=True)
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
            ext_id = binder.to_backend(category.id, wrap=True)
            if ext_id:
                ext_categ_ids.append({'id': ext_id})
        return ext_categ_ids

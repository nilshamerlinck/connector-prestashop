# -*- coding: utf-8 -*-
# #############################################################################
#
#   Prestashop_catalog_manager for OpenERP
#   Copyright (C) 2015Y Akretion <http://www.akretion.com>.
#   All Rights Reserved
#   @author : Benoît GUILLOT <benoit.guillot@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from openerp.addons.connector.event import on_record_create, on_record_write
from openerp.addons.connector.unit.mapper import (
    ExportMapper,
    mapping,
    changed_by,
    m2o_to_backend,
)

from openerp.addons.prestashoperpconnect.unit.export_synchronizer import (
    PrestashopExporter,
    export_record
)

from openerp.addons.prestashoperpconnect.unit.mapper import (
    TranslationPrestashopExportMapper,
)

import openerp.addons.prestashoperpconnect.consumer as prestashoperpconnect
from openerp.addons.prestashoperpconnect.connector import get_environment
from openerp.addons.prestashoperpconnect.backend import prestashop
from .wizard.export_multiple_products import get_slug


@on_record_create(model_names='prestashop.product.category')
@on_record_write(model_names='prestashop.product.category')
def prestashop_categ_export(session, model_name, record_id, vals):
    if session.context.get('connector_no_export'):
        return
    prestashoperpconnect.delay_export(session, model_name, record_id, vals)


@on_record_write(model_names='product.category')
def categ_export(session, model_name, record_id, vals):
    if session.context.get('connector_no_export'):
        return
    prestashoperpconnect.delay_export_all_bindings(
        session, model_name, record_id, vals)


@prestashop
class ProductCategoryExporter(PrestashopExporter):
    _model_name = 'prestashop.product.category'

    def _export_dependencies(self):
        """Export parent of the category"""
        parent = self.erp_record.parent_id
        if parent:
            binding_extra_vals = {'link_rewrite': get_slug(parent.name)}
            self._export_dependency(parent,
                                    'prestashop.product.category',
                                    exporter_class=ProductCategoryExporter,
                                    binding_extra_vals=binding_extra_vals)
        return


@prestashop
class ProductCategoryExportMapper(TranslationPrestashopExportMapper):
    _model_name = 'prestashop.product.category'

    direct = [
        ('sequence', 'position'),
        ('is_active', 'active'),
        ('default_shop_id', 'id_default_shop'),
        (m2o_to_backend('parent_id', binding=_model_name), 'id_parent')
        ]

    @changed_by(
        'name', 'link_rewrite', 'meta_title', 'meta_description',
        'meta_keywords', 'description'
    )
    @mapping
    def translatable_fields(self, record):
        translatable_fields = [
        ('name', 'name'),
        ('link_rewrite', 'link_rewrite'),
        ('meta_title', 'meta_title'),
        ('meta_description', 'meta_description'),
        ('meta_keywords', 'meta_keywords'),
        ('description', 'description'),
        ]
        trans = TranslationPrestashopExporter(self.environment)
        translated_fields = self.convert_languages(
            trans.get_record_by_lang(record.id), translatable_fields)
        return translated_fields

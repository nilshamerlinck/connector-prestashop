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
    TranslationPrestashopExporter,
    PrestashopExporter,
    export_record
)

from openerp.addons.prestashoperpconnect.unit.mapper import (
    TranslationPrestashopExportMapper,
    PrestashopExportMapper
)

import openerp.addons.prestashoperpconnect.consumer as prestashoperpconnect
from openerp.addons.prestashoperpconnect.connector import get_environment
from openerp.addons.prestashoperpconnect.backend import prestashop
from .wizard.export_multiple_products import get_slug
from openerp.addons.connector.queue.job import job


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
    if 'image' in vals:
        export_categ_image(session, model_name, record_id, vals)



@prestashop
class ProductCategoryExporter(TranslationPrestashopExporter):
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
        trans = self.unit_for( ProductCategoryExporter)
        translated_fields = self.convert_languages(
            trans.get_record_by_lang(record.id), translatable_fields)
        return translated_fields


@prestashop
class CategImageExporter(PrestashopExporter):
    _model_name = 'prestashop.categ.image'

    def _create(self, data):
        """ Create the Prestashop record """
        if self.backend_adapter.create(data):
            return 1

    def _update(self, data):
        return 1


@prestashop
class CategImageExportMapper(PrestashopExportMapper):
    _model_name = 'prestashop.categ.image'

    @changed_by('image')
    @mapping
    def image(self, record):
        name = record.name.lower() + '.jpg'
        return {'image': record['image'], 'name': name}

    @changed_by('openerp_id')
    @mapping
    def openerp_id(self, record):
        binder = self.binder_for('prestashop.product.category')
        ext_categ_id = binder.to_backend(record.openerp_id.id, wrap=True)
        return {'categ_id': ext_categ_id}


@job
def export_categ_image(session, model_name, record_id, fields=None):
    """ Export the image of a category. """
    categ = session.env[model_name].browse(record_id)
    if categ.prestashop_image_bind_ids:
        for image in categ.prestashop_image_bind_ids:
            prestashoperpconnect.delay_export(session, 'prestashop.categ.image', image.id, {})
    else:
        for presta_categ in categ.prestashop_bind_ids:
            image = categ.env['prestashop.categ.image'].create({
                'backend_id': presta_categ.backend_id.id,
                'openerp_id': categ.id
                })
            prestashoperpconnect.delay_export(session, 'prestashop.categ.image', image.id, {})

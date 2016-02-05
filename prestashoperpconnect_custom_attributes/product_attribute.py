# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for Odoo
#   Copyright (C) 2015 Akretion (http://www.akretion.com). All Rights Reserved
#   @author Benoît GUILLOT <benoit.guillot@akretion.com>
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

from openerp import models, fields, api, _, exceptions
from openerp.addons.connector.event import on_record_create, on_record_write
from openerp.addons.prestashoperpconnect.unit.export_synchronizer import (
    export_record,
    TranslationPrestashopExporter,
    )
import openerp.addons.prestashoperpconnect.consumer as prestashoperpconnect
from openerp.addons.prestashoperpconnect.unit.binder import PrestashopModelBinder
from openerp.addons.prestashoperpconnect.unit.mapper import TranslationPrestashopExportMapper
from openerp.addons.prestashoperpconnect.backend import prestashop
from openerp.addons.prestashoperpconnect.unit.backend_adapter import GenericAdapter
from openerp.addons.connector.exception import InvalidDataError
from openerp.addons.connector.unit.mapper import (
    ExportMapper,
    mapping,
    changed_by,
)

class AttributeAttribute(models.Model):
    _inherit = 'attribute.attribute'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.attribute',
        inverse_name='openerp_id',
        string="PrestaShop Bindings"
    )


class PrestashopProductAttribute(models.Model):
    _name = 'prestashop.product.attribute'
    _inherit = 'prestashop.binding'
    _inherits = {'attribute.attribute': 'openerp_id'}
    _description = "Prestashop attribute"

    openerp_id = fields.Many2one(
        comodel_name='attribute.attribute',
        string='Product Attribute',
        required=True,
        ondelete='cascade'
    )

    #has to be different than 0 because of prestashop
    prestashop_position = fields.Integer('Prestashop Position', default=1)


class AttributeOption(models.Model):
    _inherit = 'attribute.option'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.attribute.option',
        inverse_name='openerp_id',
        string="PrestaShop Bindings"
    )


class PrestashopAttributeOption(models.Model):
    _name = 'prestashop.attribute.option'
    _inherit = 'prestashop.binding'
    _inherits = {'attribute.option': 'openerp_id'}

    openerp_id = fields.Many2one(
        comodel_name='attribute.option',
        string='Attribute Option',
        required=True,
        ondelete='cascade'
    )
    prestashop_product_attribute_id = fields.Many2one(
        comodel_name='prestashop.product.attribute',
        string='Prestashop Product Attribute',
        required=True,
        ondelete='cascade'
    )

#    @api.model
#    def create(self, vals):
#        prest_attribute_obj = self.env['prestashop.product.attribute']
#        attribute_option_obj = self.env['attribute.option']
#        option = attribute_option_obj.read(vals['openerp_id'], ['attribute_id'])
#        if option and option['attribute_id']:
#            prestashop_attributes = prest_attribute_obj.search(
#                [('backend_id', '=', vals['backend_id']),
#                 ('openerp_id', '=', option['attribute_id'][0])],
#            )
#            if prestashop_attributes:
#                vals['prestashop_product_attribute_id'] = prestashop_attributes[0]
#                return super(prestashop_attribute_option, self).create(vals)
#        raise InvalidDataError("You have to export the product attribute before "
#                               "the attribute option !")
#

@on_record_create(model_names='prestashop.product.attribute')
@on_record_create(model_names='prestashop.attribute.option')
@on_record_write(model_names='prestashop.product.attribute')
@on_record_write(model_names='prestashop.attribute.option')
def prestashop_product_attribute_created(session, model_name, record_id, vals):
    if session.context.get('connector_no_export'):
        return
    export_record.delay(session, model_name, record_id, vals, priority=20)


#@on_record_create(model_names='prestashop.attribute.option')
#def prestashop_attribute_option_created(session, model_name, record_id, vals):
#    if session.context.get('connector_no_export'):
#        return
#    export_record.delay(session, model_name, record_id, vals, priority=20)
#
#@on_record_write(model_names='prestashop.product.attribute')
#def prestashop_product_attribute_written(session, model_name, record_id, vals):
#    if session.context.get('connector_no_export'):
#        return
#    export_record.delay(session, model_name, record_id, vals, priority=20)
#
#@on_record_write(model_names='prestashop.attribute.option')
#def prestashop_attribute_option_written(session, model_name, record_id, vals):
#    if session.context.get('connector_no_export'):
#        return
#    export_record.delay(session, model_name, record_id, vals, priority=20)

@on_record_write(model_names='attribute.attribute')
@on_record_write(model_names='attribute.option')
def product_attribute_written(session, model_name, record_id, vals):
    if session.context.get('connector_no_export'):
        return
    prestashoperpconnect.delay_export_all_bindings(
        session, model_name, record_id, vals)

#@on_record_write(model_names='attribute.option')
#def attribute_option_written(session, model_name, record_id, vals):
#    if session.context.get('connector_no_export'):
#        return
#    prestashoperpconnect.delay_export_all_bindings(
#        session, model_name, record_id, vals)

@on_record_create(model_names='attribute.option')
def attribute_option_created(session, model_name, record_id, vals):
    if session.context.get('connector_no_export'):
        return
    record = session.env[model_name].browse(record_id)
    prestashop_model_name = 'prestashop.attribute.option'
    for prestashop_attribute in record.attribute_id.prestashop_bind_ids:
        binding = session.env[prestashop_model_name].create({
            'openerp_id': record_id,
            'backend_id': prestashop_attribute.backend_id.id,
            'prestashop_product_attribute_id': prestashop_attribute.id
        })


@prestashop
class ProductAttributeAdapter(GenericAdapter):
    _model_name = 'prestashop.product.attribute'
    _prestashop_model = 'product_features'
    _export_node_name = 'product_feature'


@prestashop
class AttributeOptionAdapter(GenericAdapter):
    _model_name = 'prestashop.attribute.option'
    _prestashop_model = 'product_feature_values'
    _export_node_name = 'product_feature_value'


@prestashop
class PrestashopProductAttributeBinder(PrestashopModelBinder):
    _model_name = 'prestashop.product.attribute'


@prestashop
class PrestashopAttributeOptionBinder(PrestashopModelBinder):
    _model_name = 'prestashop.attribute.option'


@prestashop
class ProductAttributeExporter(TranslationPrestashopExporter):
    _model_name = 'prestashop.product.attribute'

    def _after_export(self):
        if self.erp_record.option_ids:
            option_binder = self.binder_for('prestashop.attribute.option')
            for option in self.erp_record.option_ids:
                ext_option_id = option_binder.to_backend(option.id, wrap=True)
                if not ext_option_id:
                    self.session.env['prestashop.attribute.option'].create({
                        'openerp_id': option.id,
                        'backend_id': self.backend_record.id,
                        'prestashop_product_attribute_id': self.erp_record.id
                    })


@prestashop
class AttributeOptionExporter(TranslationPrestashopExporter):
    _model_name = 'prestashop.attribute.option'

    def _export_dependencies(self):
        """ Export the dependencies for the record"""
        prest_attribute_id = self.erp_record.prestashop_product_attribute_id.id
        # export product attribute
        binder = self.binder_for('prestashop.product.attribute')
        if not binder.to_backend(prest_attribute_id):
            exporter = self.unit_for(TranslationPrestashopExporter,
                                     'prestashop.product.attribute')
            exporter.run(prest_attribute_id)
        return


@prestashop
class ProductAttributeExportMapper(TranslationPrestashopExportMapper):
    _model_name = 'prestashop.product.attribute'

    direct = [
        ('prestashop_position', 'position'),
    ]

    @changed_by('field_description')
    @mapping
    def translatable_fields(self, record):
        trans = self.unit_for(TranslationPrestashopExporter)
        translated_fields = self.convert_languages(
            trans.get_record_by_lang(record.id), [('field_description', 'name')])
        return translated_fields


@prestashop
class AttributeOptionExportMapper(TranslationPrestashopExportMapper):
    _model_name = 'prestashop.attribute.option'

    @changed_by('attribute_id', 'prestashop_product_attribute_id')
    @mapping
    def prestashop_product_attribute_id(self, record):
        return {
            'id_feature': record.prestashop_product_attribute_id.prestashop_id
        }

    @changed_by('name')
    @mapping
    def translatable_fields(self, record):
        trans = self.unit_for(TranslationPrestashopExporter)
        translated_fields = self.convert_languages(
            trans.get_record_by_lang(record.id), [('name', 'value')])
        return translated_fields

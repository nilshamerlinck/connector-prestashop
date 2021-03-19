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

from openerp.addons.connector.queue.job import job
from openerp.addons.connector.event import on_record_create, on_record_write
from openerp.addons.connector.unit.mapper import ExportMapper, mapping

from openerp.addons.prestashoperpconnect.unit.export_synchronizer import (
    TranslationPrestashopExporter,
    export_record
)

from openerp.addons.prestashoperpconnect_catalog_manager.product import ProductTemplateExportMapper
from openerp.addons.prestashoperpconnect.connector import get_environment
from openerp.addons.prestashoperpconnect.backend import prestashop
import openerp.addons.decimal_precision as dp


@prestashop
class ProductExport(TranslationPrestashopExporter):
    _model_name = 'prestashop.product.product'

    def _export_dependencies(self):
        """ Export the dependencies for the product"""
        attribute_binder = self.binder_for('prestashop.product.attribute')
        option_binder = self.binder_for('prestashop.attribute.option')
        for group in self.erp_record.attribute_group_ids:
            for attribute in group.attribute_ids:
                attribute_ext_id = attribute_binder.to_backend(
                    attribute.attribute_id.id, unwrap=True
                )
                if attribute_ext_id and attribute.ttype == 'many2one':
                    option = self.erp_record[attribute.name]
                    if option and not option_binder.to_backend(option.id, unwrap=True):
                        ctx = self.session.context.copy()
                        ctx['connector_no_export'] = True
                        option_obj = self.session.env['prestashop.attribute.option']
                        binding_id = option_obj.with_context(ctx).create(
                            {
                             'backend_id': self.backend_record.id,
                             'openerp_id': option.id,
                        })
                        export_record(
                            self.session,
                            'prestashop.attribute.option',
                            binding_id
                        )


@prestashop(replacing=ProductTemplateExportMapper)
class ProductTemplateAttributesExportMapper(ProductTemplateExportMapper):
    _model_name = 'prestashop.product.template'

    def get_changed_by_fields(self):
        fields = super(ProductTemplateAttributesExportMapper, self).get_changed_by_fields()
        attribute_obj = self.session.env['prestashop.product.attribute']
        attribute_fields = []
        for attribute in attribute_obj.search(
                [('backend_id', '=', self.backend_record.id)]):
            attribute_fields.append(attribute.name)
        return fields.union(set(attribute_fields))

    def _get_product_feature(self, record):
        product_feature = []
        attribute_binder = self.binder_for('prestashop.product.attribute')
        option_binder = self.binder_for('prestashop.attribute.option')
        for group in record.attribute_group_ids:
            for attribute in group.attribute_ids:
                attribute_ext_id = attribute_binder.to_backend(
                    attribute.attribute_id.id, wrap=True
                )
                if not attribute_ext_id:
                    continue
                feature_dict = {'id': attribute_ext_id}
                if attribute.ttype == 'many2one':
                    option = record[attribute.name]
                    if option:
                        feature_dict['id_feature_value'] = \
                            option_binder.to_backend(option.id, wrap=True)
                    else:
                        continue
                else:
                    if attribute.ttype == 'char':
                        # in case of char, prestapyt will fail sending empty values
                        if not record[attribute.name]:
                            continue
                    feature_dict['id_feature_value'] = 0
                    if attribute.translate:
                        res = self.convert_languages(
                            [(attribute.name, 'custom_feature_value')]
                        )
                    else:
                        res = {'custom_feature_value': {'language': [{'attrs': {'id': '1'}, 'value': record[attribute.name]}, {'attrs': {'id': '4'}, 'value': record[attribute.name]}]}}
                    feature_dict.update(res)
                product_feature.append(feature_dict)
        return product_feature

    @mapping
    def associations(self, record):
        res = super(ProductTemplateAttributesExportMapper, self).associations(record)
        features = res['associations']['product_features']['product_feature'] + self._get_product_feature(record)
        res['associations']['product_features']['product_feature'] = features
        return res

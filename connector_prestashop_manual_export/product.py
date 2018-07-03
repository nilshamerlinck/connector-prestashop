# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __odoo__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2015 Akretion (http://www.akretion.com).
#
##############################################################################
from odoo import models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def write(self, vals):
        """
        Don't trigger automatic export.
        """
        if 'image_ids' in vals:
            return super(ProductTemplate, self).write(vals)
        return super(
            ProductTemplate,
            self.with_context(connector_no_export=True)).write(vals)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def write(self, vals):
        """
        Don't trigger automatic export.
        """
        if 'image_ids' in vals:
            return super(ProductProduct, self).write(vals)
        return super(
            ProductProduct,
            self.with_context(connector_no_export=True)).write(vals)


class PrestashopProductTemplate(models.Model):
    _inherit = 'prestashop.product.template'

    @api.model
    def create(self, vals):
        """
        Don't trigger automatic export.
        """
        if 'image_ids' in vals:
            return super(PrestashopProductTemplate, self).write(vals)
        return super(
            PrestashopProductTemplate,
            self.with_context(connector_no_export=True)).create(vals)

    @api.multi
    def write(self, vals):
        """
        Don't trigger automatic export.
        """
        if 'image_ids' in vals or 'quantity' in vals or 'out_of_stock' in vals:
            return super(PrestashopProductTemplate, self).write(vals)
        return super(
            PrestashopProductTemplate,
            self.with_context(connector_no_export=True)).write(vals)

    @api.multi
    def export_product(self):
        for product in self:
            product.with_delay().export_record()
        return True


class PrestashopProductCombination(models.Model):
    _inherit = 'prestashop.product.combination'

    @api.model
    def create(self, vals):
        """
        Don't trigger automatic export.
        """
        if 'image_ids' in vals:
            return super(PrestashopProductCombination, self).write(vals)
        return super(
            PrestashopProductCombination,
            self.with_context(connector_no_export=True)).create(vals)

    @api.multi
    def write(self, vals):
        """
        Don't trigger automatic export.
        """
        if 'image_ids' in vals or 'quantity' in vals or 'out_of_stock' in vals:
            return super(PrestashopProductCombination, self).write(vals)
        return super(
            PrestashopProductCombination,
            self.with_context(connector_no_export=True)).write(vals)

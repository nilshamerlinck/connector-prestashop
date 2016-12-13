# -*- coding: utf-8 -*-
##############################################################################
#
#  licence AGPL version 3 or later
#  see licence in __openerp__.py or http://www.gnu.org/licenses/agpl-3.0.txt
#  Copyright (C) 2015 Akretion (http://www.akretion.com).
#
##############################################################################
from openerp import models, api, fields, exceptions, _
from openerp.addons.connector.session import ConnectorSession
import openerp.addons.prestashoperpconnect.consumer as prestashoperpconnect


class ExportMultipleProducts(models.TransientModel):
    _inherit = 'export.multiple.products'

    @api.model
    def _get_default_shop(self):
        shops = self.env['prestashop.shop'].search([])
        return shops and shops[0].id or None

    shop = fields.Many2one(default=_get_default_shop)

    @api.onchange('shop')
    def onchange_shop(self):
        if not self.shop:
            return
        self.name = self.shop.backend_id.id

    @api.multi
    def export_products(self):
        """
        Force creation of a job because the on_recordcreate/write
        are desactivated.
        """
        model = 'prestashop.product.template'
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        for product_id in self.env.context['active_ids']:
            presta_product = self.env[model].search(
                [('backend_id', '=', self.name.id),
                 ('openerp_id', '=', product_id)])
            if not presta_product:
                product = self.env['product.template'].browse(product_id)
                raise exceptions.Warning(
                    _(u"The product %s has no prestashop bindings" % product.default_code))
            if self._context.get('export') in ['all', 'product']:
                prestashoperpconnect.delay_export(
                    session, model, presta_product.id, {})
            if self._context.get('export') in ['all', 'image']:
                prestashoperpconnect.delay_export(
                    session, 'prestashop.product.image',
                    presta_product.id, {}, eta=60*1)

    @api.multi
    def export_all(self):
        self.with_context(export='all').export_products()

    @api.multi
    def export_image(self):
        self.with_context(export='image').export_products()

    @api.multi
    def export_product(self):
        self.with_context(export='product').export_products()

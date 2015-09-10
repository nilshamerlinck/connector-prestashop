# -*- coding: utf-8 -*-
###############################################################################
#
#   prestashoperpconnect_order_import for OpenERP
#   Copyright (C) 2014 Akretion (http://www.akretion.com). All Rights Reserved
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

from openerp import models, api, fields, _, exceptions
from openerp.addons.prestashoperpconnect.unit.backend_adapter import GenericAdapter
from openerp.addons.prestashoperpconnect.unit.import_synchronizer import import_record
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.prestashoperpconnect.connector import get_environment


class SaleOrderImportWizard(models.TransientModel):
    _name = 'order.import.wizard'
    _description = 'order import wizard'

    order_reference = fields.Char()

    @api.multi
    def import_order(self):
        company = self.env.user.company_id
        backend = self.env['prestashop.backend'].search(
            [('company_id', '=', company.id)])
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        env = get_environment(session, 'prestashop.sale.order', backend.id)
        adapter = env.get_connector_unit(GenericAdapter)
        filters = {'filter[reference]': self.order_reference}
        presta_id = adapter.search(filters)
        if presta_id:
            import_record(session, 'prestashop.sale.order',
                          backend.id, presta_id[0])
        else:
            raise exceptions.Warning(
                _('This sale order does not exist in the prestashop backend'))

        binder = adapter.binder_for('prestashop.sale.order')
        new_order_id = binder.to_openerp(presta_id[0], unwrap=True)
        model, view_id = self.env['ir.model.data'].get_object_reference(
            'sale', 'view_order_form')
        return {
            'name': 'Sale order',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'domain': [],
            'res_model': 'sale.order',
            'res_id': new_order_id,
            'type': 'ir.actions.act_window',
        }

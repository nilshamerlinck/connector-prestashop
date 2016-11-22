# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) All Rights Reserved 2015 Akretion
#    @author Florian da Costa <florian.dacosta@akretion.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _
import netsvc
import base64
from openerp import SUPERUSER_ID


class PrestashopSaleOrder(orm.Model):
    _inherit = "prestashop.sale.order"

    _columns = {
        'mail_sent': fields.boolean('Mail Sent'),
    }

    # can be called by prestashop to get invoice pdf and give it to customer
    # on the website
    # It should be called by a dummy user used only for prestashop, openerp
    # superuser will execute the function
    def get_invoices(self, cr, uid, prestashop_id, api_key, context=None):
        res = False
        backend_obj = self.pool['prestashop.backend']
        backend_id = backend_obj.search(
                cr, SUPERUSER_ID, [('webservice_key', '=', api_key)])
        if not backend_id:
            return res
        backend = backend_obj.browse(
                cr, SUPERUSER_ID, backend_id[0], context=context)
        user = backend.company_id.automatic_action_user_id.id
        presta_order_ids = self.search(cr, user,
                [('prestashop_id', '=', prestashop_id),
                 ('backend_id', 'in', backend_id)], context=context)
        if presta_order_ids:
            report_service = 'report.' + 'account.invoice'
            presta_order = self.browse(
                    cr, user, presta_order_ids[0], context=context)
            inv_ids = []
            for invoice in presta_order.openerp_id.invoice_ids:
                if invoice.state in ('draft', 'cancel'):
                    continue
                inv_ids.append(invoice.id)
            if inv_ids:
                service = netsvc.LocalService(report_service)
                (result, format) = service.create(
                        cr, user, inv_ids, {'model': 'account.invoice'},
                        context=context)
                res = base64.b64encode(result)
        return res
        

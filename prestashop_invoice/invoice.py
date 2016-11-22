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


class AccountInvoice(orm.Model):
    _inherit = "account.invoice"

    _columns = {
        'mail_sent': fields.boolean('Mail Sent'),
    }

    def send_prestashop_mail(self, cr, uid, ids, context=None):
        template_obj = self.pool['email.template']
        for invoice in self.browse(cr, uid, ids, context=context):
            if invoice.mail_sent:
                continue
            if not invoice.type == 'out_invoice':
                continue
            presta_sale = False
            if invoice.sale_ids:
                sale = invoice.sale_ids[0]
                if sale.prestashop_bind_ids:
                    presta_sale = sale.prestashop_bind_ids[0]
            if presta_sale and presta_sale.backend_id.invoice_tmpl_mail_id:
                if not 'default_composition_mode' in context:
                    context['default_composition_mode'] = ''
                template_obj.send_mail(
                    cr, uid, presta_sale.backend_id.invoice_tmpl_mail_id.id,
                    invoice.id, force_send=False, context=context)
                invoice.write({'mail_sent': True})
            return True

    def invoice_validate(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = super(AccountInvoice, self).invoice_validate(
                cr, uid, ids, context=context)
        self.send_prestashop_mail(cr, uid, ids, context=context)
        return res


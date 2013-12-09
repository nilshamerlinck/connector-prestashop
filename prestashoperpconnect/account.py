# -*- encoding: utf-8 -*-

from decimal import Decimal

from openerp import netsvc
from openerp.osv import fields
from openerp.osv import orm

from openerp.addons.connector.unit.mapper import mapping

from .backend import prestashop
from .unit.backend_adapter import GenericAdapter
from .unit.mapper import PrestashopImportMapper
from .unit.import_synchronizer import PrestashopImportSynchronizer


class account_invoice(orm.Model):
    _inherit = 'account.invoice'

    _columns = {
        'prestashop_bind_ids': fields.one2many(
            'prestashop.account.invoice',
            'openerp_id',
            string="Prestashop Bindings"
        ),
    }


class prestashop_refund(orm.Model):
    _name = 'prestashop.refund'
    _inherit = 'prestashop.binding'
    _inherits = {'account.invoice': 'openerp_id'}

    _columns = {
        'openerp_id': fields.many2one(
            'account.invoice',
            string='Invoice',
            required=True,
            ondelete='cascade',
        ),
        'prestashop_refund_ids': fields.one2many(
            'prestashop.refund.line',
            'prestashop_refund_id',
            'Prestashop refund lines'
        ),
    }


@prestashop
class RefundAdapter(GenericAdapter):
    _model_name = 'prestashop.refund'
    _prestashop_model = 'order_slips'


@prestashop
class RefundImport(PrestashopImportSynchronizer):
    _model_name = 'prestashop.refund'

    def _import_dependencies(self):
        record = self.prestashop_record
        self._check_dependency(record['id_customer'], 'prestashop.res.partner')
        self._check_dependency(record['id_order'], 'prestashop.sale.order')

    def _after_import(self, erp_id):
        invoice_obj = self.session.pool.get('account.invoice')
        invoice_obj.button_reset_taxes(self.session.cr, self.session.uid, [erp_id], context=self.session.context)

        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(self.session.uid, 'account.invoice',
                                erp_id, 'invoice_open', self.session.cr)


@prestashop
class RefundMapper(PrestashopImportMapper):
    _model_name = 'prestashop.refund'

    @mapping
    def journal_id(self, record):
        journal_ids = self.session.search('account.journal', [
            ('company_id', '=', self.backend_record.company_id.id),
            ('type', '=', 'sale_refund'),
        ])
        return {'journal_id': journal_ids[0]}

    @mapping
    def invoice_lines(self, record):
        slip_details = record.get('associations', {}).get('order_slip_details', []).get('order_slip_detail', [])
        if isinstance(slip_details, dict):
            slip_details = [slip_details]
        lines = []
        shipping_line = self._invoice_line_shipping(record)
        lines.append((0, 0, shipping_line))
        for slip_detail in slip_details:
            line = self._invoice_line(slip_detail)
            lines.append((0, 0, line))
        return {'invoice_line': lines}

    def _invoice_line_shipping(self, record):
        order_line = self._get_shipping_order_line(record)
        return {
            'quantity': 1,
            'product_id': order_line['product_id'][0],
            'name': order_line['name'],
            'invoice_line_tax_id': [(6, 0, order_line['tax_id'])],
            'price_unit': record['shipping_cost_amount'],
            'discount': order_line['discount'],
        }

    def _get_shipping_order_line(self, record):
        binder = self.get_binder_for_model('prestashop.sale.order')
        sale_order_id = binder.to_openerp(record['id_order'], unwrap=True)
        sale_order = self.session.browse('prestashop.sale.order', sale_order_id)

        sale_order_line_ids = self.session.search('sale.order.line', [
            ('order_id', '=', sale_order_id),
            ('product_id', '=', sale_order.carrier_id.product_id.id),
        ])
        return self.session.read('sale.order.line', sale_order_line_ids[0], [])

    def _invoice_line(self, record):
        order_line = self._get_order_line(record['id_order_detail'])
        return {
            'quantity': record['product_quantity'],
            'product_id': order_line['product_id'][0],
            'name': order_line['name'],
            'invoice_line_tax_id': [(6, 0, order_line['tax_id'])],
            'price_unit': order_line['price_unit'],
            'discount': order_line['discount'],
        }

    def _get_order_line(self, order_details_id):
        order_line_id = self.session.search('prestashop.sale.order.line', [
            ('prestashop_id', '=', order_details_id),
            ('backend_id', '=', self.backend_record.id),
        ])
        return self.session.read('prestashop.sale.order.line',
                                 order_line_id[0], [])

    @mapping
    def type(self, record):
        return {'type': 'out_refund'}

    @mapping
    def partner_id(self, record):
        binder = self.get_binder_for_model('prestashop.res.partner')
        partner_id = binder.to_openerp(record['id_customer'], unwrap=True)
        return {'partner_id': partner_id}

    @mapping
    def account_id(self, record):
        binder = self.get_binder_for_model('prestashop.res.partner')
        partner_id = binder.to_openerp(record['id_customer'])
        partner = self.session.browse('prestashop.res.partner', partner_id)
        return {'account_id': partner.property_account_receivable.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


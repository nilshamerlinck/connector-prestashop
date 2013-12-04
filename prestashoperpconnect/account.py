
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


class account_invoice_line(orm.Model):
    _inherit = 'account.invoice.line'

    _columns = {
        'prestashop_bind_ids': fields.one2many(
            'prestashop.refund.line',
            'openerp_id',
            string="Prestashop Bindings"
        ),
    }


class prestashop_refund_line(orm.Model):
    _name = 'prestashop.refund.line'
    _inherit = 'prestashop.binding'
    _inherits = {'account.invoice.line': 'openerp_id'}

    _columns = {
        'openerp_id': fields.many2one(
            'account.invoice.line',
            string='Invoice lines',
            required=True,
            ondelete='cascade'
        ),
        'prestashop_refund_id': fields.many2one(
            'prestashop.refund',
            'Prestashop Refund',
            required=True,
            ondelete='cascade',
            select=True
        ),
    }


@prestashop
class RefundAdapter(GenericAdapter):
    _model_name = 'prestashop.refund'
    _prestashop_model = 'order_slips'


@prestashop
class RefundLineAdapter(GenericAdapter):
    _model_name = 'prestashop.refund.line'
    _prestashop_model = 'order_slip_details'


@prestashop
class RefundImport(PrestashopImportSynchronizer):
    _model_name = 'prestashop.refund'

    def _import_dependencies(self):
        record = self.prestashop_record
        self._check_dependency(record['id_customer'], 'prestashop.res.partner')
        self._check_dependency(record['id_order'], 'prestashop.sale.order')


@prestashop
class RefundLineImport(PrestashopImportSynchronizer):
    _model_name = 'prestashop.refund.line'


@prestashop
class RefundMapper(PrestashopImportMapper):
    _model_name = 'prestashop.refund'

    #journal_id

    def _invoice_lines_children(self, record):
        lines_adapter = self.get_connector_unit_for_model(
            GenericAdapter, 'prestashop.refund.line')
        filters = {'filter[id_order_slip]': record['id']}
        lines = []
        for line_id in lines_adapter.search(filters=filters):
            lines.append(lines_adapter.read(line_id))
        return lines

    children = [
        (
            _invoice_lines_children,
            'prestashop_refund_ids',
            'prestashop.refund.line'
        ),
    ]

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
        # récupérer la commande
        binder = self.get_binder_for_model('prestashop.sale.order')
        order_id = binder.to_openerp(record['id_order'])
        order = self.session.read('prestashop.sale.order', order_id)

        # récupérer la facture
        invoice_ids = self.session.search('account.invoice', [
            ('origin', '=', order['name']),
            ('company_id', '=', self.backend_record.company_id.id),
        ])
        if len(invoice_ids) != 1:
            return {}
        invoice = self.session.read('account.invoice', invoice_ids[0],
                                    ['account_id'])
        # retourner le compte de la facture
        return {'account_id': invoice['account_id']}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@prestashop
class AccountInvoiceLineMapper(PrestashopImportMapper):
    _model_name = 'prestashop.refund.line'

    direct = [
        ('product_quantity', 'quantity'),
    ]

    @mapping
    def from_order_line(self, record):
        binder = self.get_binder_for_model('prestashop.sale.order.line')
        order_line_id = binder.to_openerp(record['id_order_detail'])
        order_line = self.session.read('prestashop.sale.order.line',
                                       order_line_id)
        return {
            'product_id': order_line['product_id'],
            'name': order_line['name'],
            'invoice_line_tax_id': [(6, 0, order_line['tax_id'])],
            'price_unit': order_line['price_unit'],
            'discount': order_line['discount'],
        }

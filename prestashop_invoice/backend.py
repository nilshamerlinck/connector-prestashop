from openerp.osv import orm, fields


class PrestashopBackend(orm.Model):
    _inherit = 'prestashop.backend'

    _columns = {
        'invoice_tmpl_mail_id': fields.many2one('email.template', string="Invoice Mail Template")
    }

# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.component.core import Component


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    prestashop_bind_ids = fields.One2many(
        comodel_name="prestashop.mrp.bom",
        inverse_name="odoo_id",
        string="PrestaShop Bindings",
    )


class PrestashopMrpBom(models.Model):
    _name = "prestashop.mrp.bom"
    _inherit = "prestashop.binding.odoo"
    _inherits = {"mrp.bom": "odoo_id"}
    _description = "Boms prstashop bindings"

    odoo_id = fields.Many2one(
        comodel_name="mrp.bom",
        required=True,
        ondelete="cascade",
        string="Invoice",
    )


class BomAdapter(Component):
    _name = "prestashop.bom.adapter"
    _apply_on = "prestashop.mrp.bom"
    _inherit = "prestashop.adapter"
    _prestashop_model = "products"

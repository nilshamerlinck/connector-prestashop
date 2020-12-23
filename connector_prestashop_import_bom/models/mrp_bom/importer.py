# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create


class BomMapper(Component):
    _name = "prestashop.bom.mapper"
    _inherit = "prestashop.import.mapper"
    _apply_on = "prestashop.mrp.bom"

    @mapping
    def static(self, record):
        return {
            "type": "phantom",
            "product_qty": 1,
        }

    @mapping
    def backend_id(self, record):
        return {"backend_id": self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {"company_id": self.backend_record.company_id.id}

    @only_create
    @mapping
    def product_tmpl_id(self, record):
        tmpl_binder = self.binder_for("prestashop.product.template")
        template = tmpl_binder.to_internal(record["id"], unwrap=True)
        return {
            "product_tmpl_id": template.id,
            "product_uom": template.uom_id.id,
        }

    @mapping
    def bom_lines(self, record):
        lines_vals = []
        bundle = record.get("associations", {}).get("product_bundle", {})

        binder_bom = self.binder_for("prestashop.mrp.bom")
        bom = binder_bom.to_internal(record["id"], unwrap=True)
        if bom:
            lines = bom.bom_line_ids
            lines.unlink()
        if "product" not in bundle:
            return {}
        template_binder = self.binder_for("prestashop.product.template")
        components = bundle["product"]
        if not isinstance(components, list):
            components = [components]
        for component in components:
            template = template_binder.to_internal(component["id"], unwrap=True)
            # not possible to have bom with combination component in
            # prestashop?
            variant = template.product_variant_ids[0]
            lines_vals.append(
                (
                    0,
                    0,
                    {
                        "product_id": variant.id,
                        "product_qty": int(component["quantity"]) or 1,
                        "product_uom": variant.uom_id.id,
                    },
                )
            )
        return {"bom_line_ids": lines_vals}


class BomImporter(Component):
    _name = "prestashop.bom.importer"
    _inherit = "prestashop.importer"
    _apply_on = "prestashop.mrp.bom"

    def _import_dependencies(self):
        record = self.prestashop_record
        bundle = record.get("associations", {}).get("product_bundle", {})
        if "product" not in bundle:
            return
        components = bundle["product"]
        if not isinstance(components, list):
            components = [components]
        for component in components:
            self._import_dependency(component["id"], "prestashop.product.template")


class BomBinder(Component):
    _name = "prestashop.bom.binder"
    _inherit = "prestashop.binder"
    _apply_on = "prestashop.mrp.bom"

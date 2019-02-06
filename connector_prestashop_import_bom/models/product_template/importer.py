# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component


class ProductTemplateImporter(Component):
    _inherit = 'prestashop.product.template.importer'

    def check_bom(self, binding):
        if not (self.prestashop_record['type'].get('value', '') == 'pack' or \
                self.prestashop_record['type'] == 'pack'):
            binder_bom = self.binder_for('prestashop.mrp.bom')
            bom = binder_bom.to_internal(self.prestashop_record['id'])
            if bom:
                bom.write({'active': False})

    def _after_import(self, binding):
        super(ProductTemplateImporter, self)._after_import(binding)
        self.import_bom()
        self.check_bom(binding)

    def import_bom(self):
        record = self._get_prestashop_data()
        bundle = record.get('associations', {}).get('product_bundle', {})
        if 'product' not in bundle:
            return
        self._import_dependency(record['id'],
                                'prestashop.mrp.bom',
                                always=True)


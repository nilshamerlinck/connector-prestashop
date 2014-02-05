# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP 
#   Copyright (C) 2013 Akretion (http://www.akretion.com).
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
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

from openerp.addons.prestashoperpconnect.backend import prestashop
from openerp.addons.prestashoperpconnect.unit.import_synchronizer import SaleOrderImport 
from openerp.addons.connector.connector import install_in_connector
from openerp.addons.prestashoperpconnect.unit.backend_adapter import GenericAdapter


install_in_connector()


@prestashop(replacing=SaleOrderImport)
class SaleOrderImportTransaction(SaleOrderImport):

    def _after_import(self, erp_id):
        super(SaleOrderImportTransaction, self)._after_import(erp_id)
        #For now we only support one transaction id per order
        #On OpenERP side. It's the majority of case in e-commerce
        payment_adapter = self.get_connector_unit_for_model(
            GenericAdapter,
            '__not_exist_prestashop.payment'
        )
        payment_ids = payment_adapter.search({
            'filter[order_reference]': self.prestashop_record['reference']
        })
        if payment_ids:
            payment = payment_adapter.read(payment_ids[0])
            self.session.write(self.model._name, [erp_id], {
                'transaction_id': payment['transaction_id']
                })



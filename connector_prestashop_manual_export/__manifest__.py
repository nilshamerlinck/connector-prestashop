# -*- coding: utf-8 -*-
# Copyright 2018 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


{
    'name': 'connector_prestashop_manual_export',
    "version": "10.0.1.0.0",
    'license': 'AGPL-3',
    "author": "Akretion,"
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/connector-prestashop",
    "category": "Connector",
    'depends': ['connector_prestashop_catalog_manager'],
    'data': [
        'wizard/product_export_view.xml',
        'product_view.xml',
    ],
    'demo': [],
    'installable': True,
}


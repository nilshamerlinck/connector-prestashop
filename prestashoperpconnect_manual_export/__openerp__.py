# -*- coding: utf-8 -*-
###############################################################################
#
#   prestashoperpconnect_manual_export for OpenERP
#   Copyright (C) 2014 Akretion (http://www.akretion.com). All Rights Reserved
#   @author Benoît GUILLOT <benoit.guillot@akretion.com>
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



{
    'name': 'prestashoperpconnect_manual_export',
    'version': '0.1',
    'category': 'Generic Modules/Others',
    'license': 'AGPL-3',
    'author': 'Akretion',
    'website': 'http://www.akretion.com/',
    'depends': ['prestashoperpconnect_catalog_manager'],
    'data': [
        'wizard/product_export_view.xml',
        'product_view.xml',
    ],
    'demo': [],
    'installable': True,
}


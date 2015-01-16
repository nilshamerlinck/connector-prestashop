# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Florian da Costa
#    Copyright 2015 Akretion
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
##############################################################################

{'name': 'Prestashop Connector - Export BOM stock',
 'version': '0.2',
 'category': 'Connector',
 'depends': ['prestashoperpconnect',
             'bom_stock',
             ],
 'author': 'Akretion',
 'license': 'AGPL-3',
 'website': 'http://www.akretion.com',
 'description': """
Prestashop Connector - Export Prices
===========================
Extension for **Prestashop Connector**.

When the stock of a component changes, update the stock in prestashop also for
the associated packs. 
""",
 'images': [],
 'demo': [],
 'data': [
          ],
 'installable': True,
 'application': False,
 }

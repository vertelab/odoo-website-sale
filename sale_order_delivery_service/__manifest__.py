# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo SA, Open Source Management Solution, third party addon
#    Copyright (C) 2022- Vertel AB (<https://vertel.se>).
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
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Website Sale: Show Delivery for Service Products',
    'version': '14.0.0.0.0',
    'summary': 'Module Show Delivery for Products of type Service.',
    'category': 'Website',
    'description': """
    Module Show Delivery for Products of type Service.
    """,
    'author': 'Vertel AB',
    'website': 'https://vertel.se/apps/odoo-website-sale/sale_order_delivery_service',
    'license': 'AGPL-3',
    'contributor': '',
    'maintainer': 'Vertel AB',
    'repository': 'https://github.com/vertelab/odoo-website-sale',
    # Any module necessary for this one to work correctly

    'depends': ['sale', 'product', 'website_sale', 'delivery', 'website_sale_delivery'],
    'data': [
        'views/templates.xml'
    ],
    'installable': True,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

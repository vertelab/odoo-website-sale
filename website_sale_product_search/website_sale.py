# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2017 Vertel AB (<http://vertel.se>).
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
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp import http
from openerp.http import request
import openerp.addons.website_sale.controllers.main

import logging
_logger = logging.getLogger(__name__)

class website_sale(openerp.addons.website_sale.controllers.main.website_sale):
    
    def _get_search_domain(self, search, category, attrib_values):
        domain = request.website.sale_product_domain()

        if search:
            search_fields = request.env['ir.config_parameter'].get_param('alt.product.search.fields', 'name description description_sale product_variant_ids.default_code').split(" ")
            for srch in search.split(" "):
                domain += ['|' for x in range(len(search_fields) - 1)] + [(f, 'ilike', srch) for f in search_fields]
        if category and request.env['ir.config_parameter'].get_param('alt.product.search.use_category', '1') == '1':
            domain += [('public_categ_ids', 'child_of', int(category))]

        if attrib_values:
            attrib = None
            ids = []
            for value in attrib_values:
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                else:
                    domain += [('attribute_line_ids.value_ids', 'in', ids)]
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domain += [('attribute_line_ids.value_ids', 'in', ids)]

        return domain

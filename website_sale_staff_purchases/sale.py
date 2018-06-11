# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 20178- Vertel AB (<http://vertel.se>).
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

import openerp
from openerp import http
from openerp.http import request

from openerp.addons.website_sale.controllers.main import website_sale, QueryURL, table_compute

import logging
_logger = logging.getLogger(__name__)

class WebsiteSale(website_sale):
    
    
    def checkout_values(self, data=None):
        values = super(WebsiteSale,self).checkout_values(data)
        employee_id = request.env['he.employee'].search('user_id', '=',request.website.user_id.id)
        if employee_id and employee_id.address_home_id:
            values['checkout'].update(self.checkout_parse("billing", employee_id.address_home_id))
        return values
    
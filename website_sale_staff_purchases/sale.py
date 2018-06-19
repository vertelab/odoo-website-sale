# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2018- Vertel AB (<http://vertel.se>).
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
        employee_id = request.env['hr.employee'].sudo().search([('user_id', '=',request.env.user.id)])
        if employee_id and employee_id.address_home_id:
            if not employee_id.address_home_id.is_company:
                raise Warning('Employee must be company')
            order = request.website.sale_get_order(force_create=1)
            order.partner_id = employee_id.address_home_id.id
            _logger.warn('Adresses %s' % request.env['sale.order'].sudo().onchange_partner_id(employee_id.address_home_id.id)['value'])
            order.write(request.env['sale.order'].sudo().onchange_partner_id(employee_id.address_home_id.id)['value'])
            _logger.warn('Partner_id %s shipping %s invoice %s' % (order.partner_id,order.partner_shipping_id,order.partner_invoice_id))
        res = super(WebsiteSale,self).checkout_values(data)
        order = request.website.sale_get_order(force_create=1)
        _logger.warn('Partner_id %s shipping %s invoice %s res %s' % (order.partner_id,order.partner_shipping_id,order.partner_invoice_id,res))
        return super(WebsiteSale,self).checkout_values(data)
    
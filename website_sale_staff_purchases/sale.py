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
        #TODO använd order, ändra partner_id på order (checkout_values och template skall använda order och inte user.Partner_id)
        values = super(WebsiteSale,self).checkout_values(data)
        order = values
       
        employee_id = request.env['hr.employee'].sudo().search([('user_id', '=',request.env.user.id)])
        #raise Warning(employee_id.name,request.env.user.id,request.env.user.name)
        _logger.warn('values.checkout %s user %s ' % (values.get('checkout'),{key:getattr(employee_id.address_home_id,key) for key in ['street','street2','name','zip','city']}))
        _logger.warn('values %s checkout %s' % (request.env.user.id,employee_id))
        if employee_id and employee_id.address_home_id:
            _logger.warn('values %s checkout %s' % (values.get('checkout'),employee_id))
            values['checkout'].update(self.checkout_parse("billing", {key:getattr(employee_id.address_home_id,key) for key in ['street','street2','name','zip','city']}))
            values['checkout']['invoicings'] = [employee_id.address_home_id]
            values['checkout']['shipping_name'] = employee_id.name
            values['shipping_name'] = employee_id.name
            values['vat'] = ''
            values['invoicings'] = [employee_id.address_home_id.id]
            _logger.warn('values %s checkout %s ' % (values,values.get('checkout')))
            # ~ order = self.env['sale.order'].browse(values['checkout'])
        values['checkout']['invoicing_id'] = request.env['hr.employee'].sudo().browse(59).mapped('address_home_id')[0].id
        values['checkout']['invoicings'] = [request.env['hr.employee'].sudo().browse(59).mapped('address_home_id')]
        values['invoicings'] = [request.env['hr.employee'].sudo().browse(59).mapped('address_home_id')]
        values['checkout']['shipping_name'] = 'ANDSJO'
        values['shipping_name'] = 'ANSJO'
        _logger.warn('values #end %s ' % (values))
        return values
    
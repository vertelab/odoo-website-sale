# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2017- Vertel AB (<http://vertel.se>).
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

import logging
_logger = logging.getLogger(__name__)

class sale_order_minvalue(models.Model):
    _name="sale.order.minvalue"
    
    name = fields.Char()
    destination_ids = fields.Many2many(comodel_name='res.country',string="Destinations")
    min_value = fields.Float(string="Minimum Order Value")
    info_text = fields.Text(translate=True)


class sale_order(models.Model):
    _inherit = 'sale.order'
    
    @api.one
    def _min_value_order(self):
        self.min_value_order = self.check_minimum_order_value(self,self.id)
    min_value_order = fields.Boolean(string='Minimum order value reached',compute='_min_value_order')
   
    @api.model
    def check_minimum_order_value(self,order):
        minvalue = request.env['sale.order.minvalue'].search([('destination_ids','in',sale_order.partner_shipping_id.country_id.id)],limit=1)
        if minvalue:
            return order.amount_untaxed < minvalue.min_value
        return False
        
class website(models.Model):
    _inherit = 'website'

    @api.model
    def check_minimum_order_value(self):
        sale_order = request.env['sale.order'].sudo().browse(request.session.get('sale_order_id'))
        if not sale_order:
            _logger.warning('Check minimum order value, missing sale-order %s' % request.session.get('sale_order_id'))
            return ''
        minvalue = request.env['sale.order.minvalue'].search([('destination_ids','in',sale_order.partner_shipping_id.country_id.id)],limit=1)
        if minvalue:
            if sale_order.amount_untaxed < minvalue.min_value:
                return minvalue.info_text
        return ''


#~ class website_sale(website_sale.http.Controller):

    #~ @http.route(['/shop/order/note'], type='json', auth="public", website=True)
    #~ def order_note(self, note, **post):
        #~ order = request.website.sudo().sale_get_order()
        #~ if order:
            #~ order.sudo().note = note

    #~ @http.route(['/shop/confirm_order'], type='http', auth="public", website=True)
    #~ def confirm_order(self, **post):
        #~ cr, uid, context, registry = request.cr, request.uid, request.context, request.registry

        #~ order = request.website.sale_get_order(context=context)
        #~ if not order:
            #~ return request.redirect("/shop")

        #~ redirection = self.checkout_redirection(order)
        #~ if redirection:
            #~ return redirection

        #~ values = self.checkout_values(post)

        #~ values["error"] = self.checkout_form_validate(values["checkout"])
        #~ if values["error"]:
            #~ return request.website.render("website_sale.checkout", values)

        #~ self.checkout_form_save(values["checkout"])

        #~ request.session['sale_last_order_id'] = order.id

        #~ request.website.sale_get_order(update_pricelist=True, context=context)

        #~ return request.redirect("/shop/payment")


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
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp import http
from openerp.http import request
import werkzeug
from openerp.addons.website_sale_home.website_sale import website_sale_home

import logging
_logger = logging.getLogger(__name__)



class website(models.Model):
    _inherit="website"
    
    @api.model
    def sale_home_order_get(self,user,domain):
        _logger.warn('partner %s' % user.partner_id.name)
        if not domain:
            domain = [('partner_id','child_of',user.partner_id.parent_id.id if user.partner_id.parent_id else user.partner_id.id)]
            #~ if user.partner_id.parent_id:
                #~ domain.append(('partner_id','child_of',user.partner_id.parent_id.id))
        _logger.warn('%s %s' % (domain,self.env['sale.order'].sudo().search(domain)))
        return self.env['sale.order'].sudo().search(domain)
        
    @api.model
    def sale_home_order_get_invoice(self,order):
        invoice = order.invoice_ids.mapped('id')
        #~ raise Warning(invoice,len(invoice))
        if len(invoice)>0:
            document = self.env['ir.attachment'].search([('res_id','=',invoice[0]),('res_model','=','account.invoice')]).mapped('id') 
            if len(document)>0:
                return ("/attachment/%s/%s.pdf" % (document[0],order.invoice_ids[0].origin),order.invoice_ids[0].state)
        return None
            

class website_sale_home(website_sale_home):

    @http.route(['/home/<model("res.users"):user>/order_search',], type='http', auth="user", website=True)
    def home_page_order_search(self, user=None,search=None, **post):
        self.validate_user(user)
        _logger.warn('partner %s' % user.partner_id.name)
        search_domain = [('partner_id','child_of',user.partner_id.parent_id.id if user.partner_id.parent_id else user.partner_id.id)]
        #~ if user.partner_id.parent_id:
            #~ search_domain.append(('partner_id','child_of',user.partner_id.parent_id.id))
        if search:
            for s in ['|',('name','ilike', search),'|',('date_order','ilike', search),('client_order_ref','ilike',search)]:
                search_domain.append(s)
        
       # raise Warning(search_domain,post)
        _logger.warn('search %s | domain %s | post %s',(search,search_domain,post))
        
        return request.render('website_sale_home.home_page', {
            'home_user': user if user else request.env['res.users'].browse(request.uid),
            'order_search_domain': search,
        })

    @http.route(['/home/<model("res.users"):home_user>/order/<model("sale.order"):order>',], type='http', auth="user", website=True)
    def home_page_order(self, home_user=None, order=None, **post):
        self.validate_user(home_user)
        return request.render('website_sale_home_order.page_order', {
            'home_user': home_user if home_user else request.env['res.users'].browse(request.uid),
            'order': request.env['sale.order'].browse(order.id),
        })


    @http.route(['/home/<model("res.users"):home_user>/order/<model("sale.order"):order>/copy',], type='http', auth="user", website=True)
    def home_page_order_copy(self, home_user=None,order=None, **post):
        sale_order = request.website.sale_get_order()
        if not sale_order:
            sale_order = request.website.sale_get_order(force_create=True)
        sale_order.order_line |= order.order_line
        #~ for line in order.order_line:
            #~ sale_order.order_line = [(0,0,{'product_id': line.product_id.id, 'product_uom_qty': line.product_uom_qty})]
        return werkzeug.utils.redirect("/shop/cart")

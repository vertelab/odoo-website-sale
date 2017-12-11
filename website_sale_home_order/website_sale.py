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
import math

import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit='sale.order'
    
    @api.multi
    def order_state_frontend(self):
        """Get a customer friendly order state."""
        state = None
        if self.state == 'cancel':
            state = _('Cancelled')
        elif self.state in ('shipping_except', 'invoice_except'):
            state = _('Exception')
        elif self.state in ('draft', 'sent'):
            state = _('Received')
        else:
            state = _('Packing')
            for invoice in self.invoice_ids:
                if invoice.state == 'open':
                    state = _('Shipped and invoiced')
                elif invoice.state == 'paid':
                    state = _('Paid')
        return state

class website(models.Model):
    _inherit="website"

    @api.model
    def sale_home_get_data(self, home_user, post):
        res = super(website, self).sale_home_get_data(home_user, post)
        res.update(self.sale_home_order_get(home_user, post))
        return res

    @api.model
    def sale_home_order_search_domain(self, user, search=None):
        domain = [('partner_id','child_of', user.partner_id.commercial_partner_id.id)]
        if search:
            search = search.strip()
            # invoices and picking
            orders = self.env['sale.order'].search(domain)
            invoice_ids = orders.mapped('invoice_ids').filtered(lambda i: search in i.name or search in i.number or search in i.date_invoice).mapped('id')
            picking_ids = orders.mapped('picking_ids').filtered(lambda p: search in p.name).mapped('group_id').mapped('id')
            for s in ['|', ('invoice_ids', 'in', invoice_ids), '|', ('procurement_group_id', 'in', picking_ids), '|', ('name', 'ilike', search), '|', ('date_order', 'ilike', search),'|', ('client_order_ref', 'ilike', search), ('user_id', 'ilike', search)]:
                domain.append(s)
        _logger.debug('search_domain: %s' % (domain))
        return domain

    @api.model
    def sale_home_order_get(self, user, post):
        OPP = 50 # Orders Per Page
        search = post.get('order_search')
        domain = self.sale_home_order_search_domain(user, search)
        order_page = int(post.get('order_page', '1'))
        url_args = post.copy()
        url_args.update({
            'order_page': '__ORDER_PAGE__',
            'tab': 'orders',
        })
        pager = self.pager(url='/home/%s' % user.id, total=self.env['sale.order'].search_count(domain), page=order_page, step=OPP, scope=7, url_args=url_args)
        for page in pager["pages"]:
            page['url'] = page['url'].replace('/page/%s' % page['num'], '').replace('__ORDER_PAGE__', str(page['num']))
        for page in ["page", "page_start", "page_previous", "page_next", "page_end"]:
            pager[page]['url'] = pager[page]['url'].replace('/page/%s' % pager[page]['num'], '').replace('__ORDER_PAGE__', str(pager[page]['num']))
        return {
            'sale_orders': self.env['sale.order'].search(domain, limit=OPP, offset=(order_page - 1) * OPP),
            'sale_order_pager': pager,
            'order_search': search,
        }

    @api.model
    def sale_home_order_get_invoice(self, order):
        invoice = order.invoice_ids[-1] if order and order.invoice_ids else None
        if invoice:
            document = self.env['ir.attachment'].search([('res_id', '=', invoice.id), ('res_model', '=', 'account.invoice')]).mapped('id')
            if document:
                return ('/attachment/%s/invoice.pdf' % document[-1], invoice.number, invoice.state)
            return ('', invoice.number, invoice.state)
        else:
            return ('', 'in progress...', '')

    def sale_home_order_get_picking(self, order):
        picking = order.picking_ids[-1] if order and order.picking_ids else None
        if picking:
            return ('/report/pdf/stock_delivery_slip.stock_delivery_slip/%s' % picking.id, picking.name, picking.state)
        else:
            return ('', 'in progress...', '')

class website_sale_home(website_sale_home):

    @http.route(['/home/<model("res.users"):home_user>/order/<model("sale.order"):order>',], type='http', auth="user", website=True)
    def home_page_order(self, home_user=None, order=None, tab='orders', **post):
        self.validate_user(home_user)
        return request.render('website_sale_home_order.page_order', {
            'home_user': home_user,
            'order': order,
            'tab': tab,
        })

    @http.route(['/home/<model("res.users"):home_user>/order/<model("sale.order"):order>/copy',], type='http', auth="user", website=True)
    def home_page_order_copy(self, home_user=None, order=None, **post):
        sale_order = request.website.sale_get_order()
        if not sale_order:
            sale_order = request.website.sale_get_order(force_create=True)
        #~ sale_order.order_line |= order.order_line  Bättre än nedan?
        for line in order.order_line:
            sale_order.order_line = [(0,0,{'product_id': line.product_id.id, 'product_uom_qty': line.product_uom_qty})]
        return werkzeug.utils.redirect("/shop/cart")

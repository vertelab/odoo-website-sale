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
# from openerp.addons.website_portal_sale_1028.website_sale import main website_portal_1028

import math

import logging
_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit='sale.order.line'

    @api.multi
    def sale_home_confirm_copy(self):
        """Check if this order line should be copied. Override to handle fees and whatnot."""
        return True

class SaleOrder(models.Model):
    _inherit='sale.order'

    @api.multi
    def my_order_state_frontend(self):
        """Get a customer friendly order state."""
        state = None
        if self.state == 'cancel':
            state = _('Cancelled')
        elif self.state in ('shipping_except', 'invoice_except'):
            state = _('Exception')
        elif self.state in ('sent'):
            state = _('Received')
        elif self.state in ('draft'):
            state = _('Cart')
        else:
            state = _('Ready for picking')
            for invoice in self.invoice_ids:
                if invoice.state == 'open' and invoice.residual == invoice.amount_total:
                    state = _('Shipped and invoiced')
                elif invoice.state == 'open' and invoice.residual != invoice.amount_total:
                    state = _('Partially paid')
                elif invoice.state == 'paid':
                    state = _('Paid')
        return state
        
    @api.multi
    def my_order_state_per_invoice_frontend(self):
        """Get a customer friendly order state per invoice."""
        state = []
        if self.state == 'cancel':
            state.append(_('Cancelled'))
        elif self.state in ('shipping_except', 'invoice_except'):
            state.append(_('Exception'))
        elif self.state in ('sent'):
            state.append(_('Received'))
        elif self.state in ('draft'):
            state.append(_('Cart'))
        else:
            state.append(_('Ready for picking'))
            invoices = self.invoice_ids.filtered(lambda i: i.state not in ('draft', 'proforma', 'proforma2'))
            if invoices:
                state = []
                if len(invoices) == 1:
                    if invoices[0].state == 'open' and invoices[0].residual == invoices[0].amount_total:
                        state.append(_('Shipped and invoiced'))
                    elif invoices[0].state == 'open' and invoices[0].residual != invoices[0].amount_total:
                        state.append(_('Partially paid'))
                    elif invoices[0].state == 'paid':
                        state.append(_('Paid'))
                # only print invoice numbers if there are several
                else:
                    # check if all invoices for order are fully paid.
                    if all([invoice.state == "paid" for invoice in invoices]):
                        state.append(_('Paid'))
                    else:
                        for invoice in invoices:
                            if invoice.state == 'open' and invoice.residual == invoice.amount_total:
                                state.append(_('Invoice') + ' ' + invoice.number + ': ' + _('Shipped and invoiced'))
                            elif invoice.state == 'open' and invoice.residual != invoice.amount_total:
                                state.append(_('Invoice') + ' ' + invoice.number + ': ' + _('Partially paid'))
                            elif invoice.state == 'paid':
                                state.append(_('Invoice') + ' ' + invoice.number + ': ' + _('Paid'))
        return state

class website(models.Model):
    _inherit="website"

    @api.model
    def my_orders_get_data(self, home_user, post):
        # Använd ej!
        res = super(website, self).my_orders_get_data(home_user, post)
        res.update(self.portal_my_orders(home_user, post))
        filters = self.my_order_get_all_filters(home_user)
        for filter in filters:
            if post.get(filter['id']):
                filter['active'] = True
        res['order_filters'] = filters
        return res

    @api.model
    def my_order_get_all_filters(self, user):
        # /odoo-website-sale/website_sale_home_order/website_sale.py sale_home_order_get_all_filters
        return []
    
    @api.model
    def my_order_filter_domain(self, user, filter, value):
        """Override to implement filters."""
        # /odoo-website-sale/website_sale_home_order/website_sale.py sale_home_order_filter_domain
        return []
    
    @api.model
    def my_order_search_domain_access(self, user, search):
        """Return a domain that describes which sale orders the user has access to."""
        # /odoo-website-sale/website_sale_home_order/website_sale.py sale_home_order_search_domain_access
        return [('partner_id','child_of', user.partner_id.commercial_partner_id.id), ('state','!=','draft')]

    @api.model
    def my_order_search_domain(self, user, search=None, post=None):
        # /odoo-website-sale/website_sale_home_order/website_sale.py sale_home_order_search_domain
        domain = self.my_order_search_domain_access(user, search)
        # ~ _logger.warn('\n\ndomain: %s\n' % domain)
        post = post or {}
        if search:
            search = search.strip()
            # invoices and picking
            orders = self.env['sale.order'].sudo().search_read(domain, ['invoice_ids', 'picking_ids'])
            # ~ _logger.warn('\n\norders: %s\n' % orders)
            invoice_ids = set()
            picking_ids = set()
            for o in orders:
                invoice_ids |= set(o['invoice_ids'] or [])
                picking_ids |= set(o['picking_ids'] or [])
            # ~ _logger.warn('\ninvoice_ids: %s\npicking_ids: %s' % (invoice_ids, picking_ids))
            # TODO: Date search only works with ISO-format. Find better implementation.
            invoice_ids = [d['id'] for d in self.env['account.invoice'].sudo().search_read([
					('id', 'in', list(invoice_ids)),
					'|',
						'|',
							('name', 'ilike', search),
							('number', 'ilike', search),
						('date_invoice', 'ilike', search)
				], ['id'])]
            picking_ids = self.env['stock.picking'].sudo().search_read([('id', 'in', list(picking_ids)), ('name', 'ilike', search)], ['group_id'])
            # ~ _logger.warn('\n\ninvoice_ids: %s\n' % invoice_ids)
            # ~ _logger.warn('\n\npicking_ids: %s\ngroup_ids: %s\n' % (picking_ids, [d['group_id'][0] for d in picking_ids if d['group_id']]))
            domain += ['|', '|', '|', '|', '|',
                        ('invoice_ids', 'in', invoice_ids),
                        ('procurement_group_id', 'in', [d['group_id'][0] for d in picking_ids if d['group_id']]),
                        ('name', 'ilike', search),
                        ('date_order', 'ilike', search),
                        ('client_order_ref', 'ilike', search),
                        ('user_id', 'ilike', search)]
        for key in post:
            if key.startswith('order_filter_'):
                domain += self.my_order_filter_domain(user, key, post[key])
        # ~ _logger.debug('search_domain: %s' % (domain))
        return domain

    @api.model
    def my_order_get_invoice(self, order):
        invoice = order.invoice_ids[-1] if order and order.invoice_ids else None
        if invoice:
            document = self.env['ir.attachment'].search([('res_id', '=', invoice.id), ('res_model', '=', 'account.invoice')]).mapped('id')
            if document:
                return ('/attachment/%s/invoice.pdf' % document[-1], invoice.number, invoice.state)
            return ('', invoice.number, invoice.state)
        else:
            return ('', 'in progress...', '')

    def my_order_get_picking(self, order):
        picking = order.picking_ids[-1] if order and order.picking_ids else None
        if picking:
            return ('/report/pdf/stock_delivery_slip.stock_delivery_slip/%s' % picking.id, picking.name, picking.state)
        else:
            return ('', 'in progress...', '')

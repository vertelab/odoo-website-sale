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
from openerp.addons.website_sale.controllers.main import website_sale

import logging
_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit="sale.order.line"

    is_min_order_fee = fields.Boolean(string='Min Order Fee', help="This line is a fee for orders below minimum order price")

class sale_order_minvalue(models.Model):
    _name="sale.order.minvalue"

    name = fields.Char()
    destination_ids = fields.Many2many(comodel_name='res.country',string="Destinations")
    pricelist_ids = fields.Many2many(comodel_name="product.pricelist",string="Price Lists")
    product_id = fields.Many2one(comodel_name="product.product",string="Order Fee",help="Product for Order Fee")
    order_fee = fields.Float(string="Order Fee",related="product_id.list_price")
    min_allowed_web_order = fields.Float(string="Minimum Allowed Web Order Value",help='Orders under this value will be refused in the webshop')
    min_value = fields.Float(string="Minimum Order Value",help="Orders under this value will have an extra fee")
    info_text = fields.Text(translate=True)
    info_html = fields.Html(translate=True)
    sample_order = fields.Boolean(string="Sample order",help="Allow a sample order (first one) without any fee or block.")


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    website_order_line = fields.One2many(
            'sale.order.line', 'order_id',
            string='Order Lines displayed on Website', readonly=True,
            domain=[('is_delivery', '=', False), ('is_min_order_fee', '=', False)],
            help='Order Lines to be displayed on the website. They should not be used for computation purpose.',
        )
    @api.one
    def _min_value_order(self):
        minvalue = self.get_minimum_order_value()
        _logger.warn('minvalue: %s' % minvalue)
        self.min_order_value = not self.check_minimum_order_value(minvalue)
        self.min_order_fee = self.get_min_order_fee()
    min_order_value = fields.Boolean(string='Minimum order value', compute='_min_value_order', help="Does not meet the minimum order value!")
    min_order_fee = fields.Float(string='Minimum order fee', compute='_min_value_order')

    @api.multi
    def get_minimum_order_value(self):
        self.ensure_one()
        return self.env['sale.order.minvalue'].search([('destination_ids', 'in', [self.partner_shipping_id.country_id.id or self.env.ref('base.se').id]), ('pricelist_ids', 'in', [self.pricelist_id.id])], limit=1)

    @api.multi
    def check_minimum_order_value(self, minvalue=None):
        self.ensure_one()
        minvalue = minvalue or self.get_minimum_order_value()
        if minvalue:
            if minvalue.sample_order and self.env['sale.order'].search_count([('partner_id.commercial_partner_id', '=', self.partner_id.commercial_partner_id.id)]) == 0:
                return True
            value = 0.0
            for line in self.order_line:
                if not line.is_min_order_fee and not line.is_delivery:
                    value += line.price_subtotal
            return value >= minvalue.min_value
        return True

    @api.multi
    def check_min_allowed_web_order(self, minvalue=None):
        self.ensure_one()
        minvalue = minvalue or self.get_minimum_order_value()
        if minvalue:
            if minvalue.sample_order and self.env['sale.order'].search_count([('partner_id.commercial_partner_id', '=', self.partner_id.commercial_partner_id.id)]) == 0:
                return True
            value = 0.0
            for line in self.order_line:
                if not line.is_min_order_fee and not line.is_delivery:
                    value += line.price_subtotal
            return value >= minvalue.min_allowed_web_order
        return True

    @api.multi
    def minimum_order_get_allowed(self):
        event_line = False
        not_event_line = False
        for line in self.order_line:
            if line.event_id:
                event_line = True
            else:
                not_event_line = True
        if event_line and not not_event_line:
            return True
        else:
            return self.check_min_allowed_web_order()

    @api.multi
    def action_button_confirm(self):
        self.ensure_one()
        if self._context.get('min_order_value_dialog') and not self._context.get('min_order_value_action'):
            if not self.check_minimum_order_value():
                action = self.env['ir.actions.act_window'].for_xml_id('website_sale_minimum_order_value', 'action_minimum_order_dialog')
                action['context'] = {'default_order_id': self.id}
                return action
        if self._context.get('min_order_value_action') == 'waive':
            # Find and delete min order values if they exist
            lines = self.env['sale.order.line'].search([('order_id', '=', self.id), ('is_min_order_fee', '=', True)])
            if lines:
                lines.unlink()
        else:
            self.minimum_order_value_set()
        return super(SaleOrder,self).action_button_confirm()

    @api.multi
    def get_min_order_fee(self):
        for line in self.order_line:
            if line.is_min_order_fee:
                _logger.warn('min fee: %s' % line.price_subtotal)
                return line.price_subtotal
        return 0.0

    @api.multi
    def minimum_order_value_set(self):
        line_ids = []
        for order in self:
            del_lines = order.order_line.filtered(lambda l: l.is_min_order_fee)
            if del_lines:
                del_lines.unlink()
            if order.check_minimum_order_value():
                continue
            if order.state not in ('draft', 'sent'):
                raise Warning(_('Order not in Draft State!'), _('The order state have to be draft to add minimum order value lines.'))
            minvalue = order.get_minimum_order_value()
            price_unit = minvalue.product_id.list_price
            if order.company_id.currency_id.id != order.pricelist_id.currency_id.id:
                price_unit = self.env['res.currency'].compute(order.company_id.currency_id.id, order.pricelist_id.currency_id.id, price_unit,date=order.date_order)
            values = {
                'order_id': order.id,
                'product_uom_qty': 1,
                'product_uom': minvalue.product_id.uom_id.id,
                'product_id': minvalue.product_id.id,
                'is_min_order_fee': True,
            }
            res = self.env['sale.order.line'].product_id_change(order.pricelist_id.id, values['product_id'],
                                             qty=values['product_uom_qty'], uom=False, qty_uos=0, uos=False, name='', partner_id=order.partner_id.id,
                                             lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=order.fiscal_position.id, flag=False,)
            values.update(res['value'])
            values['price_unit'] = price_unit
            if order.order_line:
                values['sequence'] = order.order_line[-1].sequence + 1
            line_id = self.env['sale.order.line'].create(values)
            line_ids.append(line_id)
        return line_ids

    def _cart_update(self, cr, uid, ids, product_id=None, line_id=None, add_qty=0, set_qty=0, context=None, **kwargs):
        """ Override to update min order fee if quantity changed """

        values = super(SaleOrder, self)._cart_update(
            cr, uid, ids, product_id, line_id, add_qty, set_qty, context, **kwargs)

        if add_qty or set_qty is not None:
            for sale_order in self.browse(cr, uid, ids, context=context):
                sale_order.minimum_order_value_set()

        return values

class SaleOrderMinvalueDialog(models.TransientModel):
    _name = 'sale.order.minvalue.dialog'

    order_id = fields.Many2one('sale.order')

    @api.multi
    def confirm_fee(self):
        return self.order_id.with_context(min_order_value_action='confirm').action_button_confirm()

    @api.multi
    def waive_fee(self):
        return self.order_id.with_context(min_order_value_action='waive').action_button_confirm()

class website(models.Model):
    _inherit = 'website'

    @api.model
    def get_monetary_str(self, amount, currency):
        amount = ('%%%s.f' % currency.accuracy) % amount
        if currency.position == 'before':
            return '%s%s' % (currency.symbol, amount)
        return '%s %s' % (amount, currency.symbol)

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

class controller(http.Controller):

    @http.route(['/shop/allowed_order'], type='http', auth="none", website=True)
    def shop_allowed_order(self, **post):
        order = request.env['sale.order'].sudo().browse(int(post.get('order', '0')))
        if order:
            res = order.minimum_order_get_allowed()
            return '1' if res else '0'
        return '0'

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
    def sale_home_claim_get(self,user,domain):
        _logger.warn('partner %s' % user.partner_id.name)
        if not domain:
            domain = [('partner_id','child_of',user.partner_id.parent_id.id if user.partner_id.parent_id else user.partner_id.id)]
            #~ if user.partner_id.parent_id:
                #~ domain.append(('partner_id','child_of',user.partner_id.parent_id.id))
        _logger.warn('%s %s' % (domain,self.env['crm.claim'].sudo().search(domain)))
        return self.env['crm.claim'].sudo().search(domain)


class website_sale_home(website_sale_home):


    @http.route(['/home/<model("res.users"):home_user>/claim/<model("crm.claim"):claim>','/home/<model("res.users"):home_user>/claims'], type='http', auth="user", website=True)
    def home_page_claim(self, home_user=None, claim=None, **post):
        self.validate_user(home_user)
        if claim:
            return request.website.render('website_sale_home_claim.page_claim', {
            'home_user': home_user,
            'claim': claim,
        })
        return request.website.render('website_sale_home_claim.page_claims', {
            'home_user': home_user,
            'claims': request.env['crm.claim'].search([('partner_id', '=', home_user.partner_id.id)]),
        })

    @http.route([
    '/home/<model("res.users"):home_user>/order/<model("sale.order"):order>/claim','/home/<model("res.users"):home_user>/line/<model("sale.order.line"):line>/claim'
    ], type='http', auth="user", website=True)
    def home_page_claim_order(self, home_user=None, order=None, line=None, **post):
        if order:
            return request.website.render('website_sale_home_claim.claim_form', {
                'home_user': home_user,
                'claim_order': order,
                'order': order,
            })
        elif line:
            return request.website.render('website_sale_home_claim.claim_form', {
                'home_user': home_user,
                'claim_line': line,
                'order': line.order_id,
            })
        else:
            return request.website.render('website_sale_home_claim.claim_form', {})

    @http.route(['/home/<model("res.users"):home_user>/order_claim/<model("sale.order"):order>/send'], type='http', auth="user", website=True)
    def claim_order_send(self, home_user=None, order=None, **post):
        claim = request.env['crm.claim'].sudo().create({
            'name': order.name,
            'partner_id': order.partner_id.id,
            'partner_phone': order.partner_id.phone,
            'email_from': order.partner_id.email,
            'ref': 'sale.order,%s' % order.id,
            'description': post.get('description', False),
        })
        return request.website.render('website_sale_home_claim.page_claim', {
            'home_user': home_user,
            'claim': request.env['crm.claim'].browse(claim.id) if claim else None,
        })

    @http.route(['/home/<model("res.users"):home_user>/line_claim/<model("sale.order.line"):line>/send'], type='http', auth="user", website=True)
    def claim_line_send(self, home_user=None, line=None, **post):
        claim = request.env['crm.claim'].sudo().create({
            'name': line.product_id.name,
            'partner_id': line.order_id.partner_id.id,
            'partner_phone': line.order_id.partner_id.phone,
            'email_from': line.order_id.partner_id.email,
            'ref': 'product.product,%s' % line.product_id.id,
            'description': post.get('description', False),
        })
        return request.website.render('website_sale_home_claim.page_claim', {
            'home_user': home_user,
            'claim': request.env['crm.claim'].browse(claim.id) if claim else None,
        })

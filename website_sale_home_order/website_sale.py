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


class website_sale_home(website_sale_home):

    @http.route(['/home','/home/<model("res.users"):user>',], type='http', auth="user", website=True)
    def home_page(self, user=None, **post):
        self.validate_user(user)
        return request.render('website_sale_home.home_page', {
            'user': user if user else request.env['res.users'].browse(request.uid),
            'orders': request.env['sale.order'].search([('partner_id', '=', user.partner_id.id)]),
        })

    @http.route(['/home/<model("res.users"):user>/order/<model("sale.order"):order>',], type='http', auth="user", website=True)
    def home_page_order(self, user=None, order=None, **post):
        self.validate_user(user)
        return request.render('website_sale_home_order.page_order', {
            'user': user if user else request.env['res.users'].browse(request.uid),
            'order': request.env['sale.order'].browse(order.id),
        })

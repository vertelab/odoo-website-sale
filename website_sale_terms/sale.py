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


class sale_order(models.Model):
    _inherit="sale.order"
    
    accepted_terms_and_conditions = fields.Boolean('Terms & Conditions accepted')
    accepted_educational_purchase = fields.Boolean('Educational Purchase Terms accepted')
    
class website_sale(http.Controller):
    @http.route(['/shop/order/terms_and_conditions'], type='json', auth="public", website=True)
    def terms_and_conditions(self, accepted, **post):
        order = request.website.sudo().sale_get_order()
        if order:
            order.sudo().accepted_terms_and_conditions = accepted

    @http.route(['/shop/order/educational_purchase'], type='json', auth="public", website=True)
    def educational_purchase(self, accepted, **post):
        order = request.website.sudo().sale_get_order()
        if order:
            order.sudo().accepted_educational_purchase = accepted

    @http.route(['/shop/order/terms_and_conditions_reseller'], type='json', auth="public", website=True)
    def terms_and_conditions_reseller(self, accepted, **post):
        order = request.website.sudo().sale_get_order()
        if order:
            order.sudo().accepted_terms_and_conditions = accepted
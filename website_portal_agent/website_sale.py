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
from openerp.addons.website_portal_sale_1028.controllers.main import website_account
import math

import logging
_logger = logging.getLogger(__name__)

class website(models.Model):
    _inherit="website"

    @api.model
    def my_order_search_domain_access(self, user, search=None):
        domain = super(website, self).my_order_search_domain_access(user, search=search)
        parent = user.commercial_partner_id
        if not parent.agent:
            return domain
        return ['|', ('partner_id.commercial_partner_id.agents', '=', parent.id)] + domain
    
    def sale_home_check_if_agent(self, customer, agent):
        if not agent.agent:
            return False
        while customer:
            if agent in customer.agents:
                return True
            customer = customer.parent_id
        return False

    @api.model
    def my_order_get_all_filters(self, user):
        res = super(website, self).my_order_get_all_filters(user)
        if user.commercial_partner_id.agent:
            res.append({'id': 'order_filter_own_orders', 'name': _('My Orders')})
        return res

    @api.model
    def my_order_filter_domain(self, user, filter, value):
        if filter == 'order_filter_own_orders' and value:
            return [('partner_id','child_of', user.partner_id.commercial_partner_id.id)]
        return super(website, self).my_order_filter_domain(user, filter, value)

class website_sale_home(website_account):

    def check_document_access(self, report, ids):
        res = super(website_sale_home, self).check_document_access(report, ids)
        if res:
            return res
        agent = request.env.user.commercial_partner_id
        if agent.agent == True:
            # Check if documents belong to this agents customers
            if report == 'sale.report_saleorder':
                for record in request.env['sale.order'].sudo().browse(ids):
                    if not request.website.sale_home_check_if_agent(record.partner_id, agent):
                        return False
                return True
            elif report == 'account.report_invoice':
                for record in request.env['account.invoice'].sudo().browse(ids):
                    if not request.website.sale_home_check_if_agent(record.partner_id, agent):
                        return False
                return True
            elif report == 'stock_delivery_slip.stock_delivery_slip':
                for record in request.env['stock.picking'].sudo().browse(ids):
                    if not request.website.sale_home_check_if_agent(record.partner_id, agent):
                        return False
                return True
        return False

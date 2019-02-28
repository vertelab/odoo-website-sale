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

class website(models.Model):
    _inherit="website"

    @api.model
    def sale_home_order_search_domain(self, user, search=None):
        domain = super(website, self).sale_home_order_search_domain(user, search=search)
        parent = user.commercial_partner_id
        if not parent.agent:
            return domain
        i = 0
        while i < len(domain):
            if domain[i][0] == 'partner_id' and domain[i][1] == 'child_of':
                domain.insert(i, '|')
                domain.insert(i + 1, ('order_line.agents.agent', 'child_of', parent.id))
                i += 2
            i += 1
        _logger.debug('search_domain: %s' % (domain))
        return domain
    
    def sale_home_check_if_agent(self, customer, agent):
        if not agent.agent:
            return False
        while customer:
            if agent in customer.agents:
                return True
            customer = customer.parent_id
        return False

class website_sale_home(website_sale_home):

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

# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2018 Vertel (<http://vertel.se>).
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
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo import http
from odoo.http import request
import werkzeug

import logging
_logger = logging.getLogger(__name__)


class Main(http.Controller):

    @http.route('/sale/statistics', type='http', auth='user', website=True)
    def sale_statistics(self, **post):
        cols = {}
        categories = request.env['product.category'].search([])
        order_lines = request.env['sale.order.line'].search([('order_id.state', 'not in', ['draft', 'cancel'])])
        pos_order_lines = request.env['pos.order.line'].search([('order_id.state', 'not in', ['draft', 'cancel'])])
        for categ in categories:
            cols[categ.name] = {}
            for sale_team in request.env['crm.team'].search([]):
                team_today_lines = order_lines.with_context(categ_id=categ, team_id=sale_team, today=fields.Date.today()).filtered(lambda l: l.product_id.categ_id == l._context.get('categ_id') and l.order_id.team_id == l._context.get('team_id') and l.order_id.date_order[:10] == l._context.get('today'))
                team_this_month_lines = order_lines.with_context(categ_id=categ, team_id=sale_team, this_month=fields.Date.today()[:7]).filtered(lambda l: l.product_id.categ_id == l._context.get('categ_id') and l.order_id.team_id == l._context.get('team_id') and l.order_id.date_order[:7] == l._context.get('this_month'))
                cols[categ.name][sale_team.name] = tuple([
                    sum(team_today_lines.mapped('price_subtotal')) if team_today_lines else 0.0,
                    sum(team_today_lines.mapped('margin')) if team_today_lines else 0.0,
                    sum(team_this_month_lines.mapped('price_subtotal')) if team_this_month_lines else 0.0,
                    sum(team_this_month_lines.mapped('margin')) if team_this_month_lines else 0.0,
                ])
            pos_today_lines = pos_order_lines.with_context(categ_id=categ, today=fields.Date.today()).filtered(lambda l: l.product_id.categ_id == l._context.get('categ_id') and l.order_id.date_order[:10] == l._context.get('today'))
            pos_this_month_lines = pos_order_lines.with_context(categ_id=categ, this_month=fields.Date.today()[:7]).filtered(lambda l: l.product_id.categ_id == l._context.get('categ_id') and l.order_id.date_order[:7] == l._context.get('this_month'))
            cols[categ.name][_('Store')] = tuple([
                sum(pos_today_lines.mapped('price_subtotal')) if pos_today_lines else 0.0,
                sum(pos_today_lines.mapped('margin')) if pos_today_lines else 0.0,
                sum(pos_this_month_lines.mapped('price_subtotal')) if pos_this_month_lines else 0.0,
                sum(pos_this_month_lines.mapped('margin')) if pos_this_month_lines else 0.0,
            ])
        return request.render('website_sale_statistics.statistics', {'cols': cols})

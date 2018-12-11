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
from datetime import date, timedelta
import calendar
import werkzeug

import logging
_logger = logging.getLogger(__name__)


class Main(http.Controller):

    @http.route('/sale/statistics', type='http', auth='user', website=True)
    def sale_statistics(self, **post):
        return request.render('website_sale_statistics.statistics', {})

    @http.route('/sale/statistics/report', type='http', auth='user', website=True)
    def sale_statistics_report(self, **post):
        pcs = _('pc(s)')
        sale_order_date_domain = [('order_id.confirmation_date', '>=', fields.Date.today() + ' 00:00:00'), ('order_id.confirmation_date', '<=', fields.Date.today() + ' 23:59:59')]
        pos_order_date_domain = [('order_id.date_order', '>=', fields.Date.today() + ' 00:00:00'), ('order_id.date_order', '<=', fields.Date.today() + ' 23:59:59')]
        date_str = fields.Date.today()
        interval = post.get('interval')
        if interval:
            if interval == 'yesterday':
                today = fields.Date.from_string(fields.Date.today())
                yesterday = fields.Date.to_string(today - timedelta(days=1))
                sale_order_date_domain = [('order_id.confirmation_date', '>=', yesterday + ' 00:00:00'), ('order_id.confirmation_date', '<=', yesterday + ' 23:59:59')]
                pos_order_date_domain = [('order_id.date_order', '>=', yesterday + ' 00:00:00'), ('order_id.date_order', '<=', yesterday + ' 23:59:59')]
                date_str = yesterday
            if interval == 'week':
                today = fields.Date.from_string(fields.Date.today())
                monday = fields.Date.to_string(today + timedelta(days=-today.weekday(), weeks=0))
                sunday = fields.Date.to_string(today + timedelta(days=+today.weekday(), weeks=0))
                sale_order_date_domain = [('order_id.confirmation_date', '>=', monday + ' 00:00:00'), ('order_id.confirmation_date', '<=', fields.Date.today() + ' 23:59:59')]
                pos_order_date_domain = [('order_id.date_order', '>=', monday + ' 00:00:00'), ('order_id.date_order', '<=', fields.Date.today() + ' 23:59:59')]
                date_str = '%s → %s' %(monday, sunday)
            if interval == 'month':
                month_end = '%s%s' %(fields.Date.today()[:8], calendar.monthrange(int(fields.Date.today()[:4]), int(fields.Date.today()[5:7]))[1])
                sale_order_date_domain = [('order_id.confirmation_date', '>=', fields.Date.today()[:8] + '01 00:00:00'), ('order_id.confirmation_date', '<=', month_end + ' 23:59:59')]
                pos_order_date_domain = [('order_id.date_order', '>=', fields.Date.today()[:8] + '01 00:00:00'), ('order_id.date_order', '<=', month_end + ' 23:59:59')]
                date_str = '%s01 → %s' %(fields.Date.today()[:8], month_end)
            if interval == 'year':
                year_end = '%s-12-31' %fields.Date.today()[:4]
                sale_order_date_domain = [('order_id.confirmation_date', '>=', fields.Date.today()[:5] + '01-01 00:00:00'), ('order_id.confirmation_date', '<=', year_end + ' 23:59:59')]
                pos_order_date_domain = [('order_id.date_order', '>=', fields.Date.today()[:5] + '01-01 00:00:00'), ('order_id.date_order', '<=', year_end + ' 23:59:59')]
                date_str = '%s-01-01 → %s' %(fields.Date.today()[:4], year_end)
        table = {'line_total': [], 'line_count': []}
        sale_order_lines = request.env['sale.order.line'].search([('order_id.state', 'not in', ['draft', 'sent', 'cancel'])] + sale_order_date_domain)
        pos_order_lines = request.env['pos.order.line'].search([('order_id.state', 'not in', ['draft', 'cancel'])] + pos_order_date_domain)
        order_lines_total = 0.0
        order_lines_count = 0
        for sale_team in request.env['crm.team'].search([]):
            order_lines = sale_order_lines.with_context(team_id=sale_team).filtered(lambda l: l.order_id.team_id == l._context.get('team_id'))
            sale_total = sum(order_lines.mapped('price_subtotal')) if order_lines else 0.0
            sale_count = len(order_lines)
            table['line_total'].append(tuple((sale_team.name, sale_total)))
            table['line_count'].append(tuple((sale_team.name, '%s %s' %(sale_count, pcs))))
            order_lines_total += sale_total
            order_lines_count += sale_count
        pos_total = sum(pos_order_lines.mapped('price_subtotal')) if pos_order_lines else 0.0
        pos_count = len(pos_order_lines)
        table['line_total'].append(tuple((_('POS'), pos_total)))
        table['line_count'].append(tuple((_('POS'), '%s %s' %(pos_count, pcs))))
        order_lines_total += pos_total
        order_lines_count += pos_count
        table['sale_total'] = tuple((_('Sale Total'), order_lines_total))
        table['sale_count'] = tuple((_('Sale Count'), '%s %s' %(order_lines_count, pcs)))

        return request.render('website_sale_statistics.statistics_report', {'table': table, 'date_str': date_str})

    # ~ @http.route('/sale/statistics/report', type='http', auth='user', website=True)
    # ~ def sale_statistics_report(self, **post):
        # ~ cols = {}
        # ~ categories = request.env['product.category'].search([])
        # ~ order_lines = request.env['sale.order.line'].search([('order_id.state', 'not in', ['draft', 'cancel'])])
        # ~ pos_order_lines = request.env['pos.order.line'].search([('order_id.state', 'not in', ['draft', 'cancel'])])
        # ~ for categ in categories:
            # ~ cols[categ.name] = {}
            # ~ for sale_team in request.env['crm.team'].search([]):
                # ~ team_today_lines = order_lines.with_context(categ_id=categ, team_id=sale_team, today=fields.Date.today()).filtered(lambda l: l.product_id.categ_id == l._context.get('categ_id') and l.order_id.team_id == l._context.get('team_id') and l.order_id.date_order[:10] == l._context.get('today'))
                # ~ team_this_month_lines = order_lines.with_context(categ_id=categ, team_id=sale_team, this_month=fields.Date.today()[:7]).filtered(lambda l: l.product_id.categ_id == l._context.get('categ_id') and l.order_id.team_id == l._context.get('team_id') and l.order_id.date_order[:7] == l._context.get('this_month'))
                # ~ cols[categ.name][sale_team.name] = tuple([
                    # ~ sum(team_today_lines.mapped('price_subtotal')) if team_today_lines else 0.0,
                    # ~ sum(team_today_lines.mapped('margin')) if team_today_lines else 0.0,
                    # ~ sum(team_this_month_lines.mapped('price_subtotal')) if team_this_month_lines else 0.0,
                    # ~ sum(team_this_month_lines.mapped('margin')) if team_this_month_lines else 0.0,
                # ~ ])
            # ~ pos_today_lines = pos_order_lines.with_context(categ_id=categ, today=fields.Date.today()).filtered(lambda l: l.product_id.categ_id == l._context.get('categ_id') and l.order_id.date_order[:10] == l._context.get('today'))
            # ~ pos_this_month_lines = pos_order_lines.with_context(categ_id=categ, this_month=fields.Date.today()[:7]).filtered(lambda l: l.product_id.categ_id == l._context.get('categ_id') and l.order_id.date_order[:7] == l._context.get('this_month'))
            # ~ cols[categ.name][_('Store')] = tuple([
                # ~ sum(pos_today_lines.mapped('price_subtotal')) if pos_today_lines else 0.0,
                # ~ sum(pos_today_lines.mapped('margin')) if pos_today_lines else 0.0,
                # ~ sum(pos_this_month_lines.mapped('price_subtotal')) if pos_this_month_lines else 0.0,
                # ~ sum(pos_this_month_lines.mapped('margin')) if pos_this_month_lines else 0.0,
            # ~ ])
        # ~ return request.render('website_sale_statistics.statistics_report', {'cols': cols})

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

import logging
_logger = logging.getLogger(__name__)

class res_partner(models.Model):
    _inherit = 'res.partner'

    has_account = fields.Boolean(compute='_has_account', help='This partner has an account')
    is_home_admin = fields.Boolean(compute='_is_home_admin', help='This partner has home admin right')

    @api.one
    def _has_account_portal(self):
        self.has_account = True if self.env['res.users'].search([('partner_id', '=', self.id)]) else False

    @api.one
    def _is_home_admin_portal(self):
        self.is_home_admin = True if self in self.env.ref('website_sale_home.group_home_admin').users.mapped('partner_id') else False

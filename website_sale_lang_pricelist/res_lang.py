# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2018- Vertel AB (<http://vertel.se>).
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


class res_lang(models.Model):
    _inherit = 'res.lang'

    pricelist_id = fields.Many2one(comodel_name='product.pricelist', string='Price List')
    fiscal_position_id = fields.Many2one(comodel_name='account.fiscal.position', string='Fiscal Position')

class product_pricelist(models.Model):
    _inherit = 'product.pricelist'

    language_ids = fields.One2many(comodel_name='res.lang', inverse_name='pricelist_id', string='Languages')

class account_fiscal_position(models.Model):
    _inherit = 'account.fiscal.position'

    language_ids = fields.One2many(comodel_name='res.lang', inverse_name='fiscal_position_id', string='Languages')

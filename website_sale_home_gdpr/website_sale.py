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


from cStringIO import StringIO


import logging
_logger = logging.getLogger(__name__)

class website(models.Model):
    _inherit="website"

    @api.model
    def sale_home_get_data(self, home_user, post):
		values = super(website, self).sale_home_get_data(home_user, post)
		#commercial_partner_id varför ens söka på företaget och jämföra med inloggade användaren?
		# ~ dict_list = request.env['gdpr.consent'].sudo().browse(partner_id.commercial_partner_id)
		# ~ dict_list.filtered(lambda i: i.partner_id.commercial_partner_id == home_user.partner_id)
		# ~ commercial_partner = request.env['res.partner'].sudo().search([('commercial_partner_id', '=', home_user.partner_id)])
		
		values['consent_ids'] = request.env['gdpr.consent'].sudo().search([('partner_id', '=', home_user.partner_id.id)])
		_logger.warning("leo %s"%values['consent_ids'])
		_logger.warning("leo %s"%home_user.partner_id.id)
		return values

class website_sale_home(website_sale_home):

    @http.route(['/home/<model("res.users"):home_user>/gdpr/<int:consent>',
                 '/home/<model("res.users"):home_user>/gdpr'
                 ], type='http', auth="user", website=True)
    def home_page_gdpr(self, home_user=None, consent=None, tab='gdpr', **post):
        self.validate_user(home_user)

        return request.website.render('website_sale_home.home_page', request.website.sale_home_get_data(home_user, post))

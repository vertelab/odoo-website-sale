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

import logging
_logger = logging.getLogger(__name__)


class website_sale_home(http.Controller):

    def validate_user(self, user):
        if request.uid == request.env.ref('base.public_user').id:
            return request.website.render('website.403')
        if not user:
            return werkzeug.utils.redirect("/home/%s" % request.uid)

    @http.route(['/home','/home/<model("res.users"):user>',], type='http', auth="user", website=True)
    def home_page(self, user=None, **post):
        self.validate_user(user)
        return request.render('website_sale_home.home_page', {
            'user': user if user else request.env['res.users'].browse(request.uid)
        })

    @http.route(['/home/<model("res.users"):user>/info_update',], type='http', auth="user", website=True)
    def info_update(self, user=None, **post):
        self.validate_user(user)
        if post.get('user_id') == str(user.id):
            user.sudo().email = post.get('email')
            user.sudo().login = post.get('login')
            user.sudo().password = post.get('password')

            partner = user.sudo().partner_id
            partner.name = post.get('name') + ' ' + post.get('last_name')
            partner.street = post.get('street')
            partner.streets = post.get('street2')
            partner.city = post.get('city')
            partner.zip = post.get('zip')
            partner.phone = post.get('phone')
            partner.mobile = post.get('mobile')
            partner.fax = post.get('fax')
            partner.country_id = int(post.get('country_id'))
            partner.ref = post.get('ref')

            if partner.parent_id:
                partner.parent_id = post.get('company')
                partner.vat = post.get('vat')

            #~ post.get('account_holder')
            #~ post.get('account_number')
            #~ post.get('account_sort_code')
            #~ post.get('bank_name')
            #~ post.get('bank_type')
            #~ post.get('iban')
            #~ post.get('other_info')

        return werkzeug.utils.redirect("/home/%s" % request.uid)




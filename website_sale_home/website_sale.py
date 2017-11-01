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

    @http.route(['/home','/home/<model("res.users"):home_user>',], type='http', auth="user", website=True)
    def home_page(self, home_user=None, tab='settings', **post):
        self.validate_user(home_user)
        _logger.warn('User %s' % home_user.name if home_user else None)
        return request.render('website_sale_home.home_page', {
            'home_user': home_user,
            'tab': post.get('tab') if post.get('tab') else tab,
            #~ 'user': user if user else request.env['res.users'].browse(request.uid)
        })

    @http.route(['/home/<model("res.users"):home_user>/info_update',], type='http', auth="user", website=True)
    def info_update(self, home_user=None, **post):
        # update data for main partner
        self.validate_user(home_user)
        if home_user == request.env.user:
            home_user = home_user.sudo()
        home_user.email = post.get('email')
        home_user.login = post.get('login')
        if post.get('confirm_password'):
            home_user.password = post.get('password')
        #~ partner = home_user.sudo().partner_id
        #~ partner.name = post.get('name')
        #~ partner.street = post.get('street')
        #~ partner.streets = post.get('street2')
        #~ partner.city = post.get('city')
        #~ partner.zip = post.get('zip')
        #~ partner.phone = post.get('phone')
        #~ partner.mobile = post.get('mobile')
        #~ partner.fax = post.get('fax')
        #~ partner.country_id = int(post.get('country_id'))

        #~ if home_user.partner_id.is_company and len(home_user.partner_id.child_ids) > 0:
            #~ # child partner data format: mainpartnerid_childpartnerid_filedname
            #~ for child in home_user.partner_id.child_ids:
                #~ child.sudo().function = post.get('%s_function' %child.id)
                #~ child.sudo().email = post.get('%s_email' %child.id)
                #~ child.sudo().phone = post.get('%s_phone' %child.id)
                #~ child.sudo().mobile = post.get('%s_mobile' %child.id)
                #~ child.sudo().use_parent_address = post.get('%s_use_parent_address' %child.id)
                #~ child.sudo().type = post.get('%s_type' %child.id)
                #~ if post.get('%s_use_parent_address' %child.id) != 1:
                    #~ child.sudo().street = post.get('%s_street' %child.id)
                    #~ child.sudo().street2 = post.get('%s_street2' %child.id)
                    #~ child.sudo().city = post.get('%s_city' %child.id)
                    #~ child.sudo().zip = post.get('%s_zip' %child.id)
                    #~ child.sudo().country_id = int(post.get('%s_country_id' %child.id))

        #~ if home_user.partner_id.is_company and post.get('account_number') != '':
            #~ res_partner_bank_obj = request.env['res.partner.bank']
            #~ if len(home_user.partner_id.bank_ids) > 0:
                #~ bank_id = home_user.partner_id.bank_ids[0]
                #~ bank_id.state = post.get('bank_type')
                #~ bank_id.acc_number = post.get('account_number')
                #~ bank_id.bank = int(post.get('bank_name'))
                #~ bank_id.bank_name = res_partner_bank_obj.onchange_bank_id(int(post.get('bank_name')))['value'].get('bank_name', False)
                #~ bank_id.bank_bic = res_partner_bank_obj.onchange_bank_id(int(post.get('bank_name')))['value'].get('bank_bic', False)
            #~ else:
                #~ res_partner_bank_obj.create({
                    #~ 'state': post.get('bank_type'),
                    #~ 'acc_number': post.get('account_number'),
                    #~ 'partner_id': home_user.partner_id.id,
                    #~ 'bank': int(post.get('bank_name')),
                    #~ 'bank_name': res_partner_bank_obj.onchange_bank_id(int(post.get('bank_name')))['value'].get('bank_name', False),
                    #~ 'bank_bic': res_partner_bank_obj.onchange_bank_id(int(post.get('bank_name')))['value'].get('bank_bic', False),
                    #~ 'owner_name': home_user.partner_id.name,
                #~ })

        #~ post.get('account_holder')
        #~ post.get('account_number')
        #~ post.get('account_sort_code')
        #~ post.get('bank_name')
        #~ post.get('bank_type')
        #~ post.get('iban')
        #~ post.get('other_info')

        return werkzeug.utils.redirect("/home/%s" % home_user.id)




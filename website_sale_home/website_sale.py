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
import base64
import sys
import traceback

import logging
_logger = logging.getLogger(__name__)

class website(models.Model):
    _inherit="website"

    @api.model
    def sale_home_get_data(self, home_user, post):
        return {
            'home_user': home_user,
            'tab': post.get('tab', 'settings'),
            'validation': {},
        }

PARTNER_FIELDS = ['name', 'street', 'street2', 'zip', 'city', 'phone', 'email']

class website_sale_home(http.Controller):

    # can be overrided with more company field
    def get_company_post(self, post):
        value = {'name': post.get('company_name')}
        return value

    # can be overrided with more company field
    def company_fields(self):
        return ['name']

    # can be overrided with more company field
    def contact_fields(self):
        return ['name','phone','mobile','email','image','attachment']

    # can be overrided with more address type
    def get_address_type(self):
        return ['delivery', 'invoice', 'contact']

    # can be overrided with more address type
    def get_children_by_address_type(self, company):
        return {
            'delivery': company.child_ids.filtered(lambda c: c.type == 'delivery')[0] if company.child_ids.filtered(lambda c: c.type == 'delivery') else None,
            'invoice': company.child_ids.filtered(lambda c: c.type == 'invoice')[0] if company.child_ids.filtered(lambda c: c.type == 'invoice') else None
        }

    # can be overrided with more address type
    def get_children_post(self, partner_id, post):
        address_type = self.get_address_type()
        children = {}
        validations = {}
        for at in address_type:
            child = self.get_child(partner_id, at, post)
            children[at] = child['child']
            validations.update(child['validation'])
        return {'children': children, 'validations': validations}

    # can be overrided with more address type
    def get_children(self, partner_id):
        address_type = self.get_address_type()
        children = {}
        for at in address_type:
            children[at] = partner_id.child_ids.filtered(lambda c: c.type == at)
        return children

    def get_child(self, partner_id, address_type, post):
        validation = {}
        child_dict = {k.split('_')[1]:v for k,v in post.items() if k.split('_')[0] == address_type}
        if any(child_dict):
            if address_type != 'contact':
                child_dict['name'] = address_type
            child_dict['parent_id'] = partner_id.id
            child_dict['type'] = address_type
            child_dict['use_parent_address'] = False
            child = partner_id.child_ids.filtered(lambda c: c.type == address_type)
            if not child:
                child = request.env['res.partner'].sudo().create(child_dict)
            else:
                child.write(child_dict)
            for field in PARTNER_FIELDS:
                validation['%s_%s' %(address_type, field)] = 'has-success'
            return {'child': child, 'validation': validation}
        return {'child': None, 'validation': validation}

    # can be overrided with more help text
    def get_help(self):
        help = {}
        help['help_company_name'] = _('')
        help['help_delivery_street'] = _('')
        help['help_delivery_street2'] = _('')
        help['help_delivery_zip'] = _('')
        help['help_delivery_city'] = _('')
        help['help_delivery_phone'] = _('')
        help['help_delivery_email'] = _('')
        help['help_invoice_street'] = _('')
        help['help_invoice_street2'] = _('')
        help['help_invoice_zip'] = _('')
        help['help_invoice_city'] = _('')
        help['help_invoice_phone'] = _('')
        help['help_invoice_email'] = _('')
        help['help_contact_street'] = _('')
        help['help_contact_street2'] = _('')
        help['help_contact_zip'] = _('')
        help['help_contact_city'] = _('')
        help['help_contact_image'] = _('Please a picture of you. This makes it more personal.')
        help['help_contact_mobile'] = _('Contatcs Cell')
        help['help_contact_phone'] = _('Contatcs phone')
        help['help_contact_email'] = _('Please add an email address')
        help['help_contact_attachment'] = _('If you have more information or a diploma, you can attach it here. You can add more than one, but you have to save each one separate.')
        return help

    def validate_user(self, user):
        if request.uid == request.env.ref('base.public_user').id:
            return request.website.render('website.403')
        if not user:
            return werkzeug.utils.redirect("/home/%s" % request.uid)

    def update_info(self, home_user, post):
        validation = {}
        children = {}
        help = {}
        company = home_user.partner_id.commercial_partner_id
        if request.httprequest.method == 'POST':
            if not company.check_token(post.get('token')):
                return request.website.render('website.403', {})
            company.write(self.get_company_post(post))
            children_dict = self.get_children_post(company, post)
            children = children_dict['children']
            validation = children_dict['validations']
            for field in self.company_fields():
                validation['company_%s' %field] = 'has-success'
        else:
            if not company.check_token(post.get('token')):
                return request.website.render('website.403', {})
            children = self.get_children(company)
        help = self.get_help()
        value = {
            'home_user': home_user,
            'help': help,
            'validation': validation,
        }
        if any(children):
            for k,v in children.items():
                value[k] = v
        return value

    # home page, company info
    @http.route(['/home','/home/<model("res.users"):home_user>'], type='http', auth="user", website=True)
    def home_page(self, home_user=None, **post):
        _logger.warn(request.httprequest.path)
        if not home_user:
            return werkzeug.utils.redirect("/home/%s" % request.env.user.id)
        self.validate_user(home_user)
        _logger.warn('User %s' % home_user.name if home_user else None)
        company = home_user.partner_id.commercial_partner_id
        value = request.website.sale_home_get_data(home_user, post)
        value.update({
            'help': self.get_help(),
            'company_form': True,
            'contact_form': False,
        })
        value.update(self.get_children_by_address_type(company))
        return request.render('website_sale_home.home_page', value)

    # update company info
    @http.route(['/home/<model("res.users"):home_user>/info_update'], type='http', auth="user", website=True)
    def info_update(self, home_user=None, **post):
        # update data for main partner
        self.validate_user(home_user)
        if home_user == request.env.user:
            home_user = home_user.sudo()
        #~ home_user.email = post.get('email')
        #~ home_user.login = post.get('login')
        #~ if post.get('confirm_password'):
            #~ home_user.password = post.get('password')
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

        self.update_info(home_user, post)
        return werkzeug.utils.redirect("/home/%s" % home_user.id)

    # new contact, update contact
    @http.route(['/home/<model("res.users"):home_user>/contact/new', '/home/<model("res.users"):home_user>/contact/<model("res.partner"):partner>'], type='http', auth='user', website=True)
    def contact_page(self, home_user=None, partner=None, **post):
        validation = {}
        company = home_user.partner_id.commercial_partner_id
        if not company.check_token(post.get('token')):
            return request.website.render('website.403', {})
        if partner:
            if not (partner in company.child_ids):
                partner = request.env['res.partner'].sudo().browse([])

        value = request.website.sale_home_get_data(home_user, post)

        if request.httprequest.method == 'POST':
            # Values
            values = {f: post['contact_%s' % f] for f in self.contact_fields() if post.get('contact_%s' % f) and f not in ['attachment','image']}
            if post.get('image'):
                image = post['image'].read()
                values['image'] = base64.encodestring(image)
            if post.get('attachment'):
                attachment = request.env['ir.attachment'].sudo().create({
                    'name': post['attachment'].filename,
                    'res_model': 'res.partner',
                    'res_id': partner.id,
                    'datas': base64.encodestring(post['attachment'].read()),
                    'datas_fname': post['attachment'].filename,
                })
            values['parent_id'] = company.id
            # Validation and store
            for field in self.contact_fields():
                validation['contact_%s' %field] = 'has-success'
            if not values.get('contact_name'):
                validation['contact_name'] = 'has-error'
            if not 'has-error' in validation:
                if not partner:
                    if values.get('email') in request.env['res.users'].sudo().search([]).mapped('login'):
                        validation['contact_email'] = 'has-error'
                        partner = request.env['res.partner'].sudo().browse([])
                        help_dic = self.get_help()
                        help_dic['help_contact_email'] = _('This email is alreay exist. Choose another one!')
                        return request.website.render('website_sale_home.home_page', {
                            'contact': partner,
                            'help': help_dic,
                            'validation': validation,
                        })
                    try:
                        user = request.env['res.users'].sudo().with_context(no_reset_password=True).create({
                            'name': values.get('name'),
                            'login': values.get('email'),
                            'image': values.get('image'),
                        })
                        user.partner_id.sudo().write({
                            'email': values.get('email'),
                            'phone': values.get('phone'),
                            'mobile': values.get('mobile'),
                            'parent_id': values.get('parent_id'),
                        })
                        partner = user.partner_id
                    except Exception as e:
                        err = sys.exc_info()
                        error = ''.join(traceback.format_exception(err[0], err[1], err[2]))
                        _logger.info('Cannot create user %s: %s' % (values.get('name'), error))
                else:
                    partner.sudo().write(values)
                values.update({
                    'company_form': False,
                    'contact_form': True,
                })
                return werkzeug.utils.redirect('/home/%s/contact/%s?token=%s' % (home_user.id, partner.id, post.get('token')))
        else:
            value.update({
                'help': self.get_help(),
                'contact': partner,
                'validation': validation,
                'company_form': False,
                'contact_form': True,
            })
        return request.render('website_sale_home.home_page', value)

    # delete contact
    @http.route(['/home/<model("res.users"):home_user>/contact/<model("res.partner"):partner>/delete'], type='http', auth='user', website=True)
    def contact_delete(self, home_user=None, partner=None, **post):
        company = home_user.partner_id.commercial_partner_id
        if not company.check_token(post.get('token')):
            return request.website.render('website.403', {})
        if partner and partner in company.child_ids:
            user = request.env['res.users'].sudo().search([('partner_id', '=', partner.id)])
            user.unlink()
            partner.unlink()
            validation = {}
            for k in self.contact_fields():
                validation[k] = 'has-success'
        return werkzeug.utils.redirect('/home/%s' % home_user.id)

    # send reset password to contact
    @http.route(['/home/contact/pw_reset'], type='json', auth='user', website=True)
    def contact_pw_reset(self, home_user=0, partner_id=0, token='', **kw):
        home_user = request.env['res.users'].sudo().browse(home_user)
        company = home_user.partner_id.commercial_partner_id
        if not company.check_token(token):
            return werkzeug.utils.redirect('/home/%s' % home_user.id)
        user = request.env['res.users'].sudo().search([('partner_id', '=', partner_id)])
        try:
            user.action_reset_password()
            return _('Password reset has been sent to user % by email' %user.name)
        except:
            _logger.warn('Cannot send mail to %s. Please check your mail server configuration.' %user.name)
            return _('Cannot send mail to %s. Please check your mail server configuration.' %user.name)

    # delete contact attachment
    @http.route(['/home/<model("res.users"):home_user>/attachment/<int:attachment>/delete'], type='http', auth='user', website=True)
    def contact_attachment_delete(self, home_user=None, attachment=0, **post):
        company = home_user.partner_id.commercial_partner_id
        if not company.check_token(post.get('token')):
            return request.website.render('website.403', {})
        if attachment > 0:
            attachment = request.env['ir.attachment'].sudo().browse(attachment)
            if attachment.res_model == 'res.partner' and attachment.res_id != 0:
                partner = request.env['res.partner'].browse(attachment.res_id)
                if partner.parent_id == home_user.partner_id.commercial_partner_id:
                    attachment.unlink()
        return werkzeug.utils.redirect('/home/%s/contact/%s?token=%s' % (home_user.id, partner.id, post.get('token')))

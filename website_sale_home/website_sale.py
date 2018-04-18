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

    # can be overridden with more company field
    def get_company_post(self, post):
        value = {}
        return value

    # can be overridden with more company field
    def company_fields(self):
        return ['name']

    # can be overridden with more company field
    def contact_fields(self):
        return ['name','phone','mobile','email','image','attachment', 'function']

    # can be overriden with more address type
    def get_address_type(self):
        """Show these address types."""
        return ['delivery', 'invoice', 'contact']

    # can be overridden with more address type
    def get_address_types_readonly(self):
        """These address types are readonly."""
        return []

    # can be overridden with more address type
    def get_children_by_address_type(self, company):
        return {
            'delivery': company.child_ids.filtered(lambda c: c.type == 'delivery')[0] if company.child_ids.filtered(lambda c: c.type == 'delivery') else None,
            'invoice': company.child_ids.filtered(lambda c: c.type == 'invoice')[0] if company.child_ids.filtered(lambda c: c.type == 'invoice') else None
        }

    # can be overridden with more address type
    def save_children(self, partner_id, post):
        address_type = set(self.get_address_type()) - set(self.get_address_types_readonly())
        children = {}
        validations = {}
        for at in address_type:
            child = self.write_child(partner_id, at, post)
            children[at] = child['child']
            validations.update(child['validation'])
        return {'children': children, 'validations': validations}

    # can be overridden with more address type
    def get_children(self, partner_id):
        address_type = self.get_address_type()
        children = {}
        for at in address_type:
            children[at] = partner_id.child_ids.filtered(lambda c: c.type == at)
        return children

    def write_child(self, partner_id, address_type, post):
        validation = {}
        child_dict = {k.split('_', 1)[1]:v for k,v in post.items() if k.split('_')[0] == address_type}
        if any(child_dict):
            if address_type != 'contact':
                child_dict['name'] = address_type
            child_dict['parent_id'] = partner_id.id
            child_dict['type'] = address_type
            child_dict['use_parent_address'] = False
            if child_dict.get('country_id'):
                child_dict['country_id'] = int(child_dict['country_id'])
            child = partner_id.child_ids.filtered(lambda c: c.type == address_type)
            if not child:
                child = request.env['res.partner'].sudo().create(child_dict)
            else:
                child.write(child_dict)
            for field in PARTNER_FIELDS:
                validation['%s_%s' %(address_type, field)] = 'has-success'
            return {'child': child, 'validation': validation}
        return {'child': None, 'validation': validation}

    # can be overridden with more help text
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
        help['help_contact_function'] = _('')
        help['help_contact_image'] = _('Please provide a picture of yourself. This makes it more personal.')
        help['help_contact_mobile'] = _('')
        help['help_contact_phone'] = _('')
        help['help_contact_email'] = _('Your email will also be used as your login name.')
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
            if post.get('invoicetype'):
                company.write({'property_invoice_type': int(post.get('invoicetype'))})
            company.write(self.get_company_post(post))
            children_dict = self.save_children(company, post)
            children = children_dict['children']
            validation = children_dict['validations']
            for field in self.company_fields():
                validation['company_%s' %field] = 'has-success'
        else:
            if not company.check_token(post.get('token')):
                return request.website.render('website.403', {})

    # home page, company info
    @http.route(['/home','/home/<model("res.users"):home_user>'], type='http', auth="user", website=True)
    def home_page(self, home_user=None, **post):
        if not home_user:
            return werkzeug.utils.redirect("/home/%s" % request.env.user.id)
        self.validate_user(home_user)
        company = home_user.partner_id.commercial_partner_id
        value = request.website.sale_home_get_data(home_user, post)
        value.update({
            'help': self.get_help(),
            'company_form': True,
            'contact_form': False,
            'address_types_readonly': self.get_address_types_readonly(),
            'country_selection': [(country['id'], country['name']) for country in request.env['res.country'].search_read([], ['name'])],
            'default_country': (home_user and home_user.country_id and home_user.country_id.id) or (request.website.company_id and request.website.company_id.country_id and request.website.company_id.country_id.id),
            'invoice_type_selection': [(invoice_type['id'], invoice_type['name']) for invoice_type in request.env['sale_journal.invoice.type'].search_read([], ['name'])],
        })
        value.update(self.get_children_by_address_type(company))
        # pages = [{'name': 'delivery', 'string': 'Delivery Address', 'type': 'contact_form', 'fields': [{'name': 'street1', 'string': 'Street', 'readonly': False, 'placeholder': 'Street 123'}...]}...]
        return request.render('website_sale_home.home_page', value)

    # update company info
    @http.route(['/home/<model("res.users"):home_user>/info_update'], type='http', auth="user", website=True)
    def info_update(self, home_user=None, **post):
        _logger.warn(post)
        # update data for main partner
        self.validate_user(home_user)
        if home_user == request.env.user:
            home_user = home_user.sudo()
        self.update_info(home_user, post)
        return werkzeug.utils.redirect("/home/%s" % home_user.id)

    def create_contact_user(self, values):
        template = request.env.ref('website_sale_home.contact_template').sudo()
        user = template.with_context(no_reset_password=True).copy({
            'name': values.get('name'),
            'login': values.get('email'),
            'image': values.get('image'),
            'active': True,
        })
        user.partner_id.sudo().write({
            'email': values.get('email'),
            'phone': values.get('phone'),
            'mobile': values.get('mobile'),
            'parent_id': values.get('parent_id'),
        })
        return user

    # new contact, update contact
    @http.route(['/home/<model("res.users"):home_user>/contact/new', '/home/<model("res.users"):home_user>/contact/<model("res.partner"):partner>'], type='http', auth='user', website=True)
    def contact_page(self, home_user=None, partner=None, **post):
        _logger.warn('\n\ncontact_page\n')
        validation = {}
        help_dic = self.get_help()
        company = home_user.partner_id.commercial_partner_id
        if not company.check_token(post.get('token')):
            return request.website.render('website.403', {})
        if partner:
            # Why?
            if not (partner in company.child_ids):
                partner = request.env['res.partner'].sudo().browse([])

        value = request.website.sale_home_get_data(home_user, post)
        value['country_selection'] = [(country['id'], country['name']) for country in request.env['res.country'].search_read([], ['name'])]
        #~ _logger.warn(value)
        values = {}
        if request.httprequest.method == 'POST':
            # Values
            values = {f: post['contact_%s' % f] for f in self.contact_fields() if post.get('contact_%s' % f) and f not in ['attachment','image']}
            if post.get('image'):
                image = post['image'].read()
                values['image'] = base64.encodestring(image)
            # If validation fails, the uploaded image will return in image_b64 on next validation attempt.
            elif post.get('image_b64'):
                values['image'] = post.get('image_b64')
            values['parent_id'] = company.id
            # Validation and store
            for field in self.contact_fields():
                validation['contact_%s' % field] = 'has-success'
            if not values.get('name'):
                validation['contact_name'] = 'has-error'
            # Check that the email is a unique user login
            if not partner and request.env['res.users'].sudo().with_context(active_test=False).search_count([('login', '=', values.get('email'))]):
                validation['contact_email'] = 'has-error'
                help_dic['help_contact_email'] = _('This email alreay exists. Choose another one or contact the administrator.')
            elif partner and request.env['res.users'].sudo().with_context(active_test=False).search_count([('login', '=', values.get('email')), ('partner_id', '!=', partner.id)]):
                validation['contact_email'] = 'has-error'
                help_dic['help_contact_email'] = _("The email %s alreay exists. Choose another one or contact the administrator." % values.get('email'))
            if not 'has-error' in validation.values():
                if not partner:
                    # Create new partner and user.
                    try:
                        user = self.create_contact_user(values)
                        partner = user.partner_id
                    except Exception as e:
                        err = sys.exc_info()
                        error = ''.join(traceback.format_exception(err[0], err[1], err[2]))
                        _logger.info('Cannot create user %s: %s' % (values.get('name'), error))
                else:
                    # Update existing partner and user.
                    partner.sudo().write(values)
                    user = request.env['res.users'].search([('partner_id', '=', partner.id)])
                    if user.name != values['name']:
                        user.name= values['name']
                    if user.login != values['email']:
                        user.login = values['email']
                if post.get('attachment'):
                    attachment = request.env['ir.attachment'].sudo().create({
                        'name': post['attachment'].filename,
                        'res_model': 'res.partner',
                        'res_id': partner.id,
                        'datas': base64.encodestring(post['attachment'].read()),
                        'datas_fname': post['attachment'].filename,
                    })
                values.update({
                    'company_form': False,
                    'contact_form': True,
                })
                return werkzeug.utils.redirect('/home/%s/contact/%s?token=%s' % (home_user.id, partner and partner.id or 'new', post.get('token')))
        value.update({
            'help': help_dic,
            'contact': partner,
            'validation': validation,
            'contact_values': values,
            'company_form': False,
            'contact_form': True,
        })
        return request.render('website_sale_home.home_page', value)

    def check_admin(self, home_user, user=False):
        user = user or request.user
        if user.partner_id.commercial_partner_id != home_user.commercial_partner_id:
            return False
        if request.env.ref('website_sale_home.group_home_admin') not in user.groups_id:
            return False
        return True

    # delete contact
    @http.route(['/home/<model("res.users"):home_user>/contact/<model("res.partner"):partner>/delete'], type='http', method="post", auth='user', website=True)
    def contact_delete(self, home_user=None, partner=None, **post):
        #~ home_user = request.env['res.users'].browse(post.get('home_user'))
        #~ partner = request.env['res.partner'].browse(post.get('partner_id'))
        reason = post.get('reason')
        company = home_user.partner_id.commercial_partner_id
        if not company.check_token(post.get('token')):
            return request.website.render('website.403', {})
        if not check_admin(home_user):
            return request.website.render('website.403', {})
        if partner and partner in company.child_ids:
            user = request.env['res.users'].sudo().search([('partner_id', '=', partner.id)])
            if user:
                # Not allowed to delete admin user
                if check_admin(home_user, user):
                    return request.website.render('website.403', {})
                else:
                    user.active = False
                    partner.active = False
            else:
                partner.active = False
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
        _logger.warn('\n\n\n%s\n\n' % user)
        try:
            if not user:
                raise Warning(_("Contact '%s' has no user.") % partner_id)
            user.action_reset_password()
            return _(u'Password reset has been sent to user %s by email') % user.name
        except:
            err = sys.exc_info()
            error = ''.join(traceback.format_exception(err[0], err[1], err[2]))
            _logger.exception(_('Cannot send mail to %s. Please check your mail server configuration.') % user.name)
            return _('Cannot send mail to %s. Please check your mail server configuration.') % user.name

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

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
from openerp.exceptions import except_orm, Warning, RedirectWarning, AccessError
from openerp import http
from openerp.http import request
import werkzeug
import base64
import sys
import traceback
import simplejson

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
            'country_selection': [(country['id'], country['name']) for country in request.env['res.country'].search_read([], ['name'])],
            'default_country': (home_user and home_user.country_id and home_user.country_id.id) or (request.website.company_id and request.website.company_id.country_id and request.website.company_id.country_id.id),
        }

    @api.model
    def website_sale_home_access_control(self, home_user):
        def check_admin(home_user):
            if self.env.user.partner_id.commercial_partner_id != home_user.commercial_partner_id:
                return False
            if self.env.ref('website_sale_home.group_home_admin') not in self.env.user.groups_id:
                return False
            return True
        if not check_admin(home_user):
            company_admin = []
            for contact in home_user.partner_id.commercial_partner_id.child_ids.filtered(lambda c: c.type == 'contact'):
                if self.env['res.users'].search([('partner_id', '=', contact.id)]):
                    if self.env.ref('website_sale_home.group_home_admin') in self.env['res.users'].search([('partner_id', '=', contact.id)]).groups_id:
                        company_admin.append(contact.name)
            if len(company_admin) > 0:
                return _('You have not access right to edit or create contact for your company. Please contact your administrator: %s.' % ' or '.join(a for a in company_admin))
            else:
                return _('You have not access right to edit or create contact for your company. Please contact us.')
        return ''

PARTNER_FIELDS = ['name', 'street', 'street2', 'zip', 'city', 'phone', 'email']

class website_sale_home(http.Controller):

    # can be overridden with more company field
    def get_company_post(self, post):
        value = {}
        # ~ if post.get('invoicetype'):
            # ~ value['property_invoice_type'] = int(post.get('invoicetype'))
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
            'delivery': company.child_ids.filtered(lambda c: c.type == 'delivery'),
            'invoice': company.child_ids.filtered(lambda c: c.type == 'invoice'),
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
        # TODO: Implement controls for which fields can be written here. This is very not secure.
        validation = {}
        child_dict = {k.split('_', 1)[1]:v for k,v in post.items() if k.split('_')[0] == address_type}
        child_dicts = {}
        delete = []
        for key in child_dict:
            id = key.split('_', 1)[0]
            if (id[:2] == 'id' and id[2:].isdigit()) or (id[:3] == 'new' and id[3:].isdigit()):
                if (id[:2] == 'id' and id[2:].isdigit()):
                    id = int(id[2:])
                if id not in child_dicts:
                    child_dicts[id] = {}
                child_dicts[id][key.split('_', 1)[1]] = child_dict[key]
                delete.append(key)
        for key in delete:
            del child_dict[key]
        res = {'child': request.env['res.partner'].browse([]), 'validation': validation}
        if child_dict:
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
                child[0].write(child_dict)
            for field in PARTNER_FIELDS:
                validation['%s_%s' %(address_type, field)] = 'has-success'
            res['child'] |= child
        _logger.warn(child_dicts)
        for id in child_dicts:
            d = child_dicts[id]
            if address_type != 'contact':
                d['name'] = address_type
            d['parent_id'] = partner_id.id
            d['type'] = address_type
            d['use_parent_address'] = False
            if d.get('country_id'):
                d['country_id'] = int(d['country_id'])
            if type(id) == int:
                child = partner_id.child_ids.filtered(lambda c: c.type == address_type and c.id == id)
                if child:
                    child.write(d)
            else:
                child = request.env['res.partner'].sudo().create(d)
            for field in PARTNER_FIELDS:
                validation['%s_id%s_%s' %(address_type, child.id, field)] = 'has-success'
            res['child'] |= child
        return res

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
        # TODO: This does nothing?
        if request.uid == request.env.ref('base.public_user').id:
            return request.website.render('website.403')
        if not user:
            return werkzeug.utils.redirect("/home/%s" % request.uid)

    def update_info(self, home_user, post):
        if not self.check_admin(home_user):
            return request.website.render('website.403', {})
        validation = {}
        children = {}
        help = {}
        company = home_user.partner_id.commercial_partner_id
        if request.httprequest.method == 'POST':
            if post.get('website_short_description'):
                translated_text = request.env['ir.translation'].search([('name', '=', 'res.partner,website_short_description'), ('type', '=', 'model'), ('lang', '=', request.env.lang), ('res_id', '=', home_user.partner_id.commercial_partner_id.id)])
                if translated_text:
                    translated_text.write({'value': post.get('website_short_description')})
            # ~ if post.get('invoicetype'):
                # ~ company.write({'property_invoice_type': int(post.get('invoicetype'))})
            company.write(self.get_company_post(post))
            children_dict = self.save_children(company, post)
            children = children_dict['children']
            validation = children_dict['validations']
            for field in self.company_fields():
                validation['company_%s' %field] = 'has-success'

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
            'invoice_type_selection': [(invoice_type['id'], invoice_type['name']) for invoice_type in request.env['sale_journal.invoice.type'].sudo().search_read([], ['name'])],
        })
        value.update(self.get_children_by_address_type(company))
        # pages = [{'name': 'delivery', 'string': 'Delivery Address', 'type': 'contact_form', 'fields': [{'name': 'street1', 'string': 'Street', 'readonly': False, 'placeholder': 'Street 123'}...]}...]
        return request.render('website_sale_home.home_page', value)

    # update company info
    @http.route(['/home/<model("res.users"):home_user>/info_update'], type='http', auth="user", website=True)
    def info_update(self, home_user=None, **post):
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
        validation = {}
        help_dic = self.get_help()
        company = home_user.partner_id.commercial_partner_id
        if partner:
            # Why?
            if not (partner in company.child_ids):
                partner = request.env['res.partner'].sudo().browse([])

        value = request.website.sale_home_get_data(home_user, post)
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
                    if user and user.name != values['name']:
                        user.name= values['name']
                    if user and user.login != values['email']:
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
                return werkzeug.utils.redirect('/home/%s/contact/%s' % (home_user.id, partner and partner.id or 'new'))
        value.update({
            'help': help_dic,
            'contact': partner,
            'validation': validation,
            'contact_values': values,
            'company_form': False,
            'contact_form': True,
            'access_warning': '',
        })
        return request.render('website_sale_home.home_page', value)

    def check_admin(self, home_user, user=False):
        user = user or request.env.user
        if user.partner_id.commercial_partner_id != home_user.commercial_partner_id:
            return False
        if request.env.ref('website_sale_home.group_home_admin') not in user.groups_id:
            return False
        return True

    @http.route(['/home/send_message'], type='json', auth="user", website=True)
    def send_message(self, partner_id=None, msg_body='', **kw):
        partner = request.env.user.partner_id.commercial_partner_id
        if msg_body:
            if request.env.user.partner_id not in partner.message_follower_ids:
                partner.sudo().message_subscribe_users([request.env.user.id])
            msg_body = msg_body.split('\n', 1)
            subject = body = ''
            for word in msg_body[0].split(' '):
                if len(subject) < 40:
                    subject = ' '.join([subject, word])
                else:
                    body = ' '.join([body, word])
            if len(msg_body) > 1:
                body = ' '.join([body, msg_body[1]])
            partner.message_post(subject=subject, body=body, author_id=request.env.user.partner_id.id)
            return True
        return False

    def delete_contact(self, home_user, partner, reason):
        partner = partner.sudo()
        user = request.env['res.users'].sudo().search([('partner_id', '=', partner.id)])
        if user:
            # Not allowed to delete admin user
            if self.check_admin(home_user, user):
                return request.website.render('website.403', {})
            else:
                user.active = False
        body = _("""%s wants to delete <a href="/web?debug=#id=%s&view_type=form&model=res.partner">%s</a> because '%s'.""") % (request.env.user.name, partner.id, partner.name, reason)
        subject = _("Contact %s inactivated") % partner.name
        partner.commercial_partner_id.message_post(body=body, subject=subject)
        partner.message_post(body=body, subject=subject)
        partner.active = False

    # delete contact
    @http.route(['/home/<model("res.users"):home_user>/contact/<model("res.partner"):partner>/delete'], type='http', method="post", auth='user', website=True)
    def contact_delete(self, home_user=None, partner=None, **post):
        #~ home_user = request.env['res.users'].browse(post.get('home_user'))
        #~ partner = request.env['res.partner'].browse(post.get('partner_id'))
        reason = post.get('reason', '')
        company = home_user.partner_id.commercial_partner_id
        if not self.check_admin(home_user):
            return request.website.render('website.403', {})
        if partner and partner in company.child_ids:
            try:
                self.delete_contact(home_user, partner, reason)
            except AccessError:
                return request.website.render('website.403', {})
        return werkzeug.utils.redirect('/home/%s' % home_user.id)

    # send reset password to contact
    @http.route(['/home/contact/pw_reset'], type='json', auth='user', website=True)
    def contact_pw_reset(self, home_user=0, partner_id=0, **kw):
        home_user = request.env['res.users'].browse(home_user)
        company = home_user.partner_id.commercial_partner_id
        user = request.env['res.users'].sudo().search([('partner_id', '=', partner_id)])
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

    # remove contact image
    @http.route(['/home/contact/remove_img_contact'], type='json', auth="public", website=True)
    def contact_remove_img(self, partner_id='0', **kw):
        partner = request.env['res.partner'].browse(int(partner_id))
        if partner:
            partner.write({'image': None})
            return True
        return False

    # delete contact attachment
    @http.route(['/home/<model("res.users"):home_user>/attachment/<int:attachment>/delete'], type='http', auth='user', website=True)
    def contact_attachment_delete(self, home_user=None, attachment=0, **post):
        if not check_admin(home_user):
            return request.website.render('website.403', {})
        company = home_user.partner_id.commercial_partner_id
        if attachment > 0:
            attachment = request.env['ir.attachment'].sudo().browse(attachment)
            if attachment.res_model == 'res.partner' and attachment.res_id != 0:
                partner = request.env['res.partner'].browse(attachment.res_id)
                if partner.parent_id == home_user.partner_id.commercial_partner_id:
                    attachment.unlink()
        return werkzeug.utils.redirect('/home/%s/contact/%s' % (home_user.id, partner.id))

    def check_document_access(self, report, ids):
        """Override to implement access control."""
        return False
    
    @http.route(['/home/<model("res.users"):home_user>/print/<reportname>/<docids>'], type='http', auth='user', website=True)
    def print_document(self, reportname, home_user=None, docids=None, **data):
        """Creates PDF documents with sudo to avoid access rights problems.
        Implement access control per report type in check_document_access."""
        if docids:
            docids = [int(i) for i in docids.split(',')]
        if not self.check_document_access(reportname, docids):
            return request.website.render('website.403', {})
        context = {}
        options_data = None
        if data.get('options'):
            options_data = simplejson.loads(data['options'])
        if data.get('context'):
            # Ignore 'lang' here, because the context in data is the one from the webclient *but* if
            # the user explicitely wants to change the lang, this mechanism overwrites it. 
            data_context = simplejson.loads(data['context'])
            if data_context.get('lang'):
                del data_context['lang']
            context.update(data_context)
        # Version 8 of get_pdf takes a recordset but does nothing with it except fetch the ids.
        dummy = DummyRecordSet(docids)
        pdf = request.env['report'].sudo().with_context(context).get_pdf(dummy, reportname, data=options_data)
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
        return request.make_response(pdf, headers=pdfhttpheaders)

class DummyRecordSet(object):
    def __init__(self, ids):
        self.ids = ids

# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2020- Vertel AB (<http://vertel.se>).
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
from openerp import http, fields, _
from openerp.http import request
from openerp import tools
from openerp.tools.translate import _

from openerp.fields import Date
from babel.dates import format_date
from cStringIO import StringIO

import logging
_logger = logging.getLogger()

class website_account(http.Controller):

    MANDATORY_BILLING_FIELDS = ["name", "phone", "email", "street", "city", "country_id"]
    OPTIONAL_BILLING_FIELDS = ["zipcode", "state_id", "vat", "company_name"]

    _items_per_page = 20


    def get_campaign_products(self, salon=True, limit=8, page=0):
        def pretty_date(date):
            return format_date(fields.Date.from_string(date), 'd MMM', locale=request.env.context.get('lang')).replace('.', '')
        name = 'Produkt %s'
        res = []
        helpers = request.env['crm.tracking.campaign.helper'].sudo().search([
                ('for_reseller', '=', True),
                ('country_id', '=', request.env.user.partner_id.commercial_partner_id.country_id.id),
                ('salon', '=', salon),
            ], limit = limit, offset = limit * page)
        lang = request.env['res.lang'].search([('code', '=', request.env.context.get('lang'))])
        for helper in helpers:
            if helper.variant_id:
                product = helper.variant_id
                variant = helper.variant_id
            elif helper.product_id:
                product = helper.product_id
                variant = product.get_default_variant()
            else:
                # This should never happen. Lets pretend like it didn't.
                continue
            line = {
                'product': helper.campaign_id.name,
                'image': '',
                'price_origin':''
            }
            res.append(line)
            if helper.campaign_id.image:
                line['image'] = '/web/binary/image?id=%s&field=image&model=crm.tracking.campaign' % helper.campaign_id.id
            if product._name == 'product.template':
                line['url'] = '/dn_shop/product/%s' % product.id
            else:
                line['url'] = '/dn_shop/variant/%s' % product.id
            # Find the relevant phase
            if helper.salon:
                # Campaign aimed at salons
                phase = helper.campaign_phase_id
                price = variant.pricelist_chart_ids.filtered(lambda c: (c.pricelist_chart_id.pricelist == phase.pricelist_id)).rec_price    
            else:
                # Campaign aimed at consumers
                phase = helper.campaign_id.phase_ids.filtered(lambda p: not p.reseller_pricelist)[0]
                price = variant.pricelist_chart_ids.filtered(lambda c: c.pricelist_chart_id.pricelist == phase.pricelist_id).rec_price
            date_start = phase.start_date
            date_stop = phase.end_date
            if not date_stop:
                line['period'] = _('until further notice')
            elif date_start:
                line['period'] = '%s - %s' % (pretty_date(date_start),pretty_date(date_stop))
            else:
                line['period'] = '- %s' % pretty_date(date_stop)
            # Calculate customers price at campaign start
            if not price:
                line['price'] = _(' ')
            else:
                line['price'] = '%s %s' % (lang.format(
                            '%f',
                            price,
                            grouping=True, monetary=True, context=request.env.context)[:-4],
                            phase.pricelist_id.currency_id.name
                    )
        return res

    def _prepare_portal_layout_values(self):
        """ prepare the values to render portal layout """
        partner = request.env.user.partner_id
        # get customer sales rep
        if partner.user_id:
            sales_rep = partner.user_id
        else:
            sales_rep = False
        values = {
            'sales_rep': sales_rep,
            'company': request.website.company_id,
            'user': request.env.user
        }
        return values


    def _get_archive_groups(self, model, domain=None, fields=None, groupby="create_date", order="create_date desc"):
        if not model:
            return []
        if domain is None:
            domain = []
        if fields is None:
            fields = ['name', 'create_date']
        groups = []
        for group in request.env[model]._read_group_raw(domain, fields=fields, groupby=groupby, orderby=order):
            dates, label = group[groupby]
            date_begin, date_end = dates.split('/')
            groups.append({
                'date_begin': Date.to_string(Date.from_string(date_begin)),
                'date_end': Date.to_string(Date.from_string(date_end)),
                'name': label,
                'item_count': group[groupby + '_count']
            })
        return groups

    @http.route(['/my/home'], type='http', auth="user", website=True)
    def account(self, **kw):
        values = self._prepare_portal_layout_values()
        values['offers_salon'] = self.get_campaign_products(salon=True, limit=50)
        values['offers_consumer'] = self.get_campaign_products(salon=False, limit=50)
        values['my_categs'] = request.env['product.public.category'].search([('show_on_my_home', '=', True)])

        return request.render("website_portal_1028.portal_my_home", values)

    @http.route(['/my/account'], type='http', auth='user', website=True)
    def details(self, redirect=None, **post):
        partner = request.env.user.partner_id
        values = {
            'error': {},
            'error_message': []
        }

        if post:
            error, error_message = self.details_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)
            if not error:
                values = {key: post[key] for key in self.MANDATORY_BILLING_FIELDS}
                values.update({key: post[key] for key in self.OPTIONAL_BILLING_FIELDS if key in post})
                values.update({'zip': values.pop('zipcode', '')})
                partner.sudo().write(values)
                if redirect:
                    return request.redirect(redirect)
                return request.redirect('/my/home')

        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])

        values.update({
            'partner': partner,
            'countries': countries,
            'states': states,
            'has_check_vat': hasattr(request.env['res.partner'], 'check_vat'),
            'redirect': redirect,
        })

        return request.render("website_portal_1028.details", values)

    def details_form_validate(self, data):
        error = dict()
        error_message = []

        # Validation
        for field_name in self.MANDATORY_BILLING_FIELDS:
            if not data.get(field_name):
                error[field_name] = 'missing'

        # email validation
        if data.get('email') and not tools.single_email_re.match(data.get('email')):
            error["email"] = 'error'
            error_message.append(_('Invalid Email! Please enter a valid email address.'))

        # vat validation
        if data.get("vat") and hasattr(request.env["res.partner"], "check_vat"):
            if data.get("country_id"):
                data["vat"] = request.env["res.partner"].fix_eu_vat_number(int(data.get("country_id")), data.get("vat"))
            if request.website.company_id.sudo().vat_check_vies:
                # force full VIES online check
                check_func = request.env["res.partner"].vies_vat_check
            else:
                # quick and partial off-line checksum validation
                check_func = request.env["res.partner"].simple_vat_check
            vat_country, vat_number = request.env["res.partner"]._split_vat(data.get("vat"))
            if not check_func(vat_country, vat_number):  # simple_vat_check
                error["vat"] = 'error'

        # error message for empty required fields
        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))

        unknown = [k for k in data.iterkeys() if k not in self.MANDATORY_BILLING_FIELDS + self.OPTIONAL_BILLING_FIELDS]
        if unknown:
            error['common'] = 'Unknown field'
            error_message.append("Unknown field '%s'" % ','.join(unknown))

        return error, error_message

    def check_document_access(self, ids, report=None):
        """Override to implement access control."""
        if not report:
            # Documents are attachments
            # Check if the attachments are in portal catalogs that this user is allowed to see.
            allowed_ids = [a['id'] for a in request.env['ir.attachment'].sudo().search_read(
                [
                    ('id', 'in', ids),
                    ('parent_id.portal_publish', '=', True),
                    ('parent_id.group_ids.users', 'in', request.env.user.id)
                ], ['id'])]
            attachment_ids = set(ids) - set(allowed_ids)
            if attachment_ids:
                # Check if we're allowed to access remaining attachments
                # must include some field other than id to trigger access check
                allowed_ids = set([a['id'] for a in request.env['ir.attachment'].search_read([('id', 'in', list(attachment_ids))], ['id', 'name'])])
                if attachment_ids - allowed_ids:
                    # There are some attachments we're not allowed to read.
                    return False
            return True
        return False
    
    @http.route(['/my/documents/<model("res.users"):home_user>/print/<reportname>/<docids>',
                 '/my/documents/<model("res.users"):home_user>/print/<reportname>/<docids>/<docname>',
                 ], type='http', auth='user', website=True)
    def print_document(self, reportname, home_user=None, docids=None, docname=None, **data):
        """Creates PDF documents with sudo to avoid access rights problems.
        Implement access control per report type in check_document_access."""
        self.validate_user(home_user)
        if docids:
            docids = [int(i) for i in docids.split(',')]
        if not self.check_document_access(docids, report=reportname):
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

    @http.route(['/my/documents/<model("res.users"):home_user>/document/<int:document_id>',
                 '/my/documents/<model("res.users"):home_user>/document/<int:document_id>/<docname>'
                 ], type='http', auth="user", website=True)
    def download_document(self, document_id, home_user=None, docname=None, **post):
        self.validate_user(home_user)
        if self.check_document_access([document_id]):
            document = request.env['ir.attachment'].sudo().search([('id', '=', document_id)]) #TODO better security-check  check:225 ir_attachment.py  check:71 document.py
            _logger.warn('Try to send %s' % document)
            fname = (docname or document.datas_fname or document.name).encode('ascii', 'replace')
            mime = mimetype=document.mimetype or document.file_type or ''
            write_date=document.write_date
            data = document.datas.decode('base64')
            return http.send_file(StringIO(data), filename=fname, mimetype=mime, mtime=write_date, as_attachment=True)
        return request.website.render('website.403', {})

class DummyRecordSet(object):
    def __init__(self, ids):
        self.ids = ids

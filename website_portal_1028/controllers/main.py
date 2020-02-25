# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import http
from openerp.http import request
from openerp import tools
from openerp.tools.translate import _

from openerp.fields import Date


class website_account(http.Controller):

    MANDATORY_BILLING_FIELDS = ["name", "phone", "email", "street", "city", "country_id"]
    OPTIONAL_BILLING_FIELDS = ["zipcode", "state_id", "vat", "company_name"]

    _items_per_page = 20


    def get_campaign_products(self, salon=True, limit=8):
        res = [
            {
                'product': 'En produkt',
                'price': '99 kr',
                'price_origin': '199 kr',
                'period': '1 sept - 31 okt',
            }
        ]
        if salon:
            res[0]['product'] = 'En salongsprodukt'
        return res
        # request.env['crm.tracking.campaign.helper'].sudo().search([('for_reseller', '=', True), ('country_id', '=', request.env.user.partner_id.commercial_partner_id.country_id.id)])

        # ctch = request.env['crm.tracking.campaign.helper'].sudo().search([('for_reseller', '=', reseller), ('country_id', '=', request.env.user.partner_id.commercial_partner_id.country_id.id)])
        # campaign_products = request.env['product.product'].search([('id', 'in', (ctch.mapped('variant_id') | ctch.mapped('product_id').mapped('product_variant_ids')).mapped('id'))], limit=limit)
        # for campaign_product in campaign_products:
        #     helper = ctch.filtered(lambda h: h.variant_id == campaign_product) or ctch.filtered(lambda h: campaign_product in h.product_id.product_variant_ids)



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

    @http.route(['/my', '/my/home'], type='http', auth="user", website=True)
    def account(self, **kw):
        values = self._prepare_portal_layout_values()
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

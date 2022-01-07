# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import http, _, fields
from openerp.exceptions import AccessError
from openerp.http import request, Controller

#from openerp.tools.translate import _

from openerp.addons.website_portal_1028.controllers.main import website_account
# from openerp.addons.account_followup.report import website_followup
#from openerp.addons.delivery_unifaun_base import delivery
from openerp.addons.web.controllers.main import content_disposition

from openerp import api, exceptions, models
import werkzeug
import base64
import sys
import traceback
import simplejson
from math import ceil

import logging
_logger = logging.getLogger(__name__)

from cStringIO import StringIO

from openerp.report.report_sxw import report_sxw
from openerp.api import Environment

try:
    import xlsxwriter
except ImportError:
    _logger.debug('Can not import xlsxwriter`.')

PARTNER_FIELDS = ['name', 'street', 'street2', 'zip', 'city', 'phone', 'email']

class website_account(website_account):
    @http.route()
    def account(self, **kw):
        """ Add sales documents to main account page """
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id

        SaleOrder = request.env['sale.order']
        Invoice = request.env['account.invoice']
        # quotation_count = SaleOrder.search_count([
        #     ('message_follower_ids', 'child_of', [partner.commercial_partner_id.id]),
        #     ('state', 'in', ['sent', 'cancel'])
        # ])
        # order_count = SaleOrder.search_count([
        #     ('message_follower_ids', 'child_of', [partner.commercial_partner_id.id]),
        #     ('state', 'in', ['sale', 'done'])
        # ])
        invoice_count = Invoice.search_count([
            ('type', 'in', ['out_invoice', 'out_refund']),
            ('message_follower_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['open', 'paid', 'cancel'])
        ])

        response.qcontext.update({
            # 'quotation_count': quotation_count,
            # 'order_count': order_count,
            'invoice_count': invoice_count,
        })
        return response


    @http.route(['/my/orders', '/my/orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_orders(self, page=1, **post):
        home_user = request.env.user
        self.validate_user(home_user)
        values = self._prepare_portal_layout_values()
        partner = request.env.user.commercial_partner_id
        filters = request.website.my_order_get_all_filters(home_user)
        search = post.get('order_search')
        domain = request.website.my_order_search_domain(home_user, search, post)
        _logger.debug('search_domain: %s' % (domain))
        SaleOrder = request.env['sale.order']
        move_line_table = request.env['account.move.line'].sudo().search([
            ('partner_id', '=', partner.id),
            ('reconcile_id', '=', False),
            ('account_id.active','=', True),
            ('account_id.type', '=', 'receivable'),
            ('state', '!=', 'draft')])

        archive_groups = "" # DAER: Ugg not understand, Ugg remove.
        # archive_groups = self._get_archive_groups('sale.order', domain)
        # count for pager
        order_count = SaleOrder.sudo().search_count(domain)

        # The `domain` has the field invoice_ids, which does not exists
        # The line below crashes the site
        # move_line_count = move_line_table.sudo().search_count(domain)

        # pager
        pager = request.website.pager(
            url="/my/orders",
            url_args={},
            total=order_count,
            page=page,
            step=self._items_per_page,
            scope=7
        )
        # pager2 = request.website.pager(
        #     url="/my/orders",
        #     url_args={},
        #     total=move_line_count,
        #     page=page,
        #     step=self._items_per_page,
        #     scope=7
        # )
        _logger.debug('pager: %s' % (pager,))
        # content according to pager and archive selected
        orders = SaleOrder.sudo().search(domain, limit=self._items_per_page, offset=pager['offset'])
        # lines2 = move_line_table.sudo().search(domain, limit=self._items_per_page, offset=pager2['offset'])
        values.update({
            'orders': orders,
            'page_name': 'order',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/orders',
            'order_filters': filters,
            'active_menu': 'my_orders',
            'move_line_table': move_line_table,
        })
        return request.render("website_portal_sale_1028.portal_my_orders", values)


    @http.route(['/my/reseller/<int:partner_id>','/my/reseller'], type='http', website=True)
    def my_resellers(self, partner_id=None, **post):
        if not partner_id:
            partner = request.env.user.agents[0] if len(request.env.user.agents) >0 else None
        else:
            partner = request.env['res.partner'].sudo().search([('id', '=', partner_id), ('is_reseller', '=', True), ('child_ids.type', '=', 'visit')])
        values = self._prepare_portal_layout_values()

        values.update({
            'active_menu': 'my_reseller',
            'reseller': partner,
        })
        return request.render("website_portal_sale_1028.my_reseller", values)


    @http.route(['/my/credits', '/my/credits/page/<int:page>'], type='http', auth="user", website=True)
    def my_credit_invoice(self, page=1, **post):
        portal_user = request.env.user
        self.validate_user(portal_user)
        values = self._prepare_portal_layout_values()
        invoice_obj = request.env['account.invoice']
        domain = [('type', '=', 'out_refund'), ('partner_id', 'child_of', portal_user.commercial_partner_id.id)]
        pager = request.website.pager(
            url="/my/credits",
            url_args={},
            total=invoice_obj.search_count(domain),
            page=page,
            step=self._items_per_page,
            scope=7
        )
        values.update({
            'invoices': invoice_obj.search(domain, limit=self._items_per_page, offset=pager['offset']),
            'pager': pager,
            'active_menu': 'my_credit_invoice'
        })

        return request.render("website_portal_sale_1028.my_credit_invoice", values)


    @http.route(['/my/credits/<int:invoice_id>'], type='http', auth="user", website=True)
    def credits_followup(self, portal_user=None, invoice_id=None, tab='credits', **post):
        portal_user = request.env.user
        self.validate_user(portal_user)
        invoice = request.env['account.invoice'].sudo().browse(invoice_id)
        if not invoice:
            html = request.website._render(
                    'website.403',
                    {
                        'status_code': 403,
                        'status_message': werkzeug.http.HTTP_STATUS_CODES[403]
                    })
            return werkzeug.wrappers.Response(html, status=403, content_type='text/html;charset=utf-8')

        return request.render("website_portal_sale_1028.credits_followup", {
            'portal_user': request.env.user,
            'invoice': invoice,
            'tab': tab
        })

    @http.route(['/my/reclaim'], type='http', auth="user", website=True)
    def portal_my_reclaim (self, **kw):
        portal_user = request.env.user
        self.validate_user(portal_user)
        values = self._prepare_portal_layout_values()
        values.update({
            'active_menu': 'my_reclaim',
            })
        return request.render("website_portal_sale_1028.portal_my_reclaim", values)


    @http.route(['/my/products'], type='http', auth="user", website=True)
    def portal_xport (self, **kw):
        portal_user = request.env.user
        self.validate_user(portal_user)
        values = self._prepare_portal_layout_values()
        values.update({
            'active_menu': 'my_products',
            })

        return request.render("website_portal_sale_1028.portal_export_data", values)

    @http.route(['/my/products/xls'], type='http', auth="user", website=True)
    def print_product_details(self, **kw):
        portal_user = request.env.user
        self.validate_user(portal_user)
        import xlsxwriter

        output = StringIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()
        row = 0
        col = 0

        header = list(map(_,['Item number','Product','Variant attribute','EAN code','Description',u'Use description','INCI Ingredients','Width','Height','Depth','Volume','Weight','Tags/Properties','Quantity per box','Cost price','Retail price']))
        for data in header:
            worksheet.write(row, col, data)
            col += 1
        col = 0

        products = request.env['product.product'].sudo().search([('website_published','=',True), ('sale_ok','=',True), ('active','=',True)])
        partner = request.env.user.partner_id.commercial_partner_id
        pricelist = partner.property_product_pricelist

        for product in products:
            row += 1

            item = [product.default_code,
            product.name,
            ', '.join(product.attribute_value_ids.mapped('display_name')),
            product.ean13,
            product.public_desc,
            product.use_desc,
            product.ingredients,
            product.width,
            product.height,
            product.depth,
            product.volume,
            product.weight,
            ', '.join(product.facet_line_ids.mapped('value_ids.display_name')),
            product.packaging_ids.qty,
            product.get_pricelist_chart_line(pricelist).price,
            product.get_pricelist_chart_line(pricelist).rec_price,
            ]
            for data in item:
                worksheet.write(row, col, data)
                col += 1
            col = 0

        workbook.close()
        output.seek(0)
        return http.send_file(output, filename='export.xlsx', as_attachment=True, cache_timeout=0, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


    @http.route(['/my/imagearchive'], type='http', auth="user", website=True)
    def portal_my_image_archive(self, **kw):
        portal_user = request.env.user
        if portal_user.has_group('webshop_dermanord.group_dn_sk'):
            return request.website.render('website.403', {})
        self.validate_user(portal_user)
        values = self._prepare_portal_layout_values()
        values.update({
            'portal_user': portal_user,
            'active_menu': 'my_imagearchive'
        })
        return request.render("website_portal_sale_1028.portal_my_image_archive", values)

    @http.route(['/my/news'], type='http', auth="user", website=True)
    def portal_my_news(self, **kw):
        portal_user = request.env.user
        if portal_user.has_group('webshop_dermanord.group_dn_sk'):
            return request.website.render('website.403', {})
        self.validate_user(portal_user)
        values = self._prepare_portal_layout_values()
        values.update({
            'portal_user': portal_user,
            'active_menu': 'my_news'
        })
        return request.render("website_portal_sale_1028.portal_my_news", values)

    @http.route(['/my/events'], type='http', auth="user", website=True)
    def portal_my_events(self, **kw):
        portal_user = request.env.user
        if portal_user.has_group('webshop_dermanord.group_dn_sk'):
            return request.website.render('website.403', {})
        self.validate_user(portal_user)
        values = self._prepare_portal_layout_values()
        values.update({
            'portal_user': portal_user,
            'active_menu': 'my_events'
        })
        return request.render("website_portal_sale_1028.portal_my_events", values)

    @http.route(['/my/other'], type='http', auth="user", website=True)
    def portal_my_other(self, **kw):
        portal_user = request.env.user
        if portal_user.has_group('webshop_dermanord.group_dn_sk'):
            return request.website.render('website.403', {})
        self.validate_user(portal_user)
        values = self._prepare_portal_layout_values()
        values.update({
            'portal_user': portal_user,
            'active_menu': 'my_other',
            })
        return request.render("website_portal_sale_1028.portal_my_other", values)

    @http.route(['/my/compendium'], type='http', auth="user", website=True)
    def portal_my_compendium(self, **kw):
        portal_user = request.env.user
        if portal_user.has_group('webshop_dermanord.group_dn_sk'):
            return request.website.render('website.403', {})
        self.validate_user(portal_user)
        values = self._prepare_portal_layout_values()
        values.update({
            'portal_user': portal_user,
            'active_menu': 'my_compendium',
            })
        return request.render("website_portal_sale_1028.portal_my_compendium", values)

    @http.route(['/my/pricelist/pdf'], type='http', auth="user", website=True)
    def portal_my_pricelist_print(self, **kw):
        home_user = request.env.user
        if home_user.has_group('webshop_dermanord.group_dn_sk'):
           return request.website.render('website.403', {})
        self.validate_user(home_user)
        partner = request.env.user.commercial_partner_id
        report = request.env['product.pricelist.dermanord'].sudo()
        pricelist = request.env.user.commercial_partner_id.property_product_pricelist.sudo()
        pricelist_version = None
        today = fields.Date.today()
        for version in pricelist.version_id:
            if not version.active:
                continue
            if version.date_start and version.date_start > today:
                continue
            if version.date_end and version.date_end < today:
                continue
            pricelist_version = version
            break
        report = report.create({
            'date': pricelist_version.date_start and version.date_start or today,
            'pricelist_title_one': _('Your price (excl. tax)'),
            'pricelist_title_two': pricelist.rec_pricelist_id and _('Rec. price (incl. tax)') or None,
            'fiscal_position_id_one': (partner.is_company and request.env.ref('website_portal_sale_1028.fiscal_position_tax_free') or partner.property_account_position.sudo()).id,
            'fiscal_position_id_two': pricelist.rec_pricelist_id and partner.property_account_position.sudo().id or None,
            'pricelist_id_one': pricelist.id,
            'pricelist_id_two': pricelist.rec_pricelist_id and pricelist.rec_pricelist_id.id or None,

            })
        action = report.print_report()
        pdf = report.env['report'].sudo().with_context(report_lang=request.env.context.get('lang'), translatable=True).get_pdf(report.env['product.product'].browse(), action['report_name'], data=action['data'])
        # product_pricelist_dermanord.report_pricelist None {'lang': u'sv_SE', 'tz': u'Europe/Stockholm', 'uid': 1, u'active_model': u'product.pricelist.dermanord', u'translatable': True, u'report_lang': u'sv_SE', u'params': {u'action': 4209}, u'search_disable_custom_filters': True, u'active_ids': [120], u'active_id': 120}
        filename = _("Pricelist Maria Åkerberg")
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf)), ('Content-Disposition', content_disposition('%s.pdf' % filename))]
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route(['/my/pricelist'], type='http', auth="user", website=True)
    def portal_my_pricelist(self, **kw):
        home_user = request.env.user
        self.validate_user(home_user)
        values = self._prepare_portal_layout_values()
        values.update({
            'active_menu': 'my_pricelist',

            })

        return request.render("website_portal_sale_1028.portal_my_pricelist", values)

    @http.route(['/my/buyinfo'], type='http', auth="user", website=True)
    def portal_my_buy_info(self, **kw):
        values = self._prepare_portal_layout_values()
        values.update({
            'active_menu': 'my_buyinfo',
            })
        return request.render("website_portal_sale_1028.portal_my_buy_info", values)

    @http.route(['/my/obsolete'], type='http', auth="user", website=True)
    def portal_my_obsolete(self, **kw):
        values = self._prepare_portal_layout_values()
        values.update({
            'active_menu': 'my_obsolete',
            })

        return request.render("website_portal_sale_1028.portal_my_obsolete", values)

    def get_mailing_lists(self, email):
        mailing_lists = []
        for mailing_list in request.env['mail.mass_mailing.list'].sudo().search([('website_published', '=', True),('country_ids','in',request.env.user.partner_id.commercial_partner_id.country_id.id)]):
            mailing_lists.append({
                'name': mailing_list.name,
                'id': mailing_list.id,
                'subscribed': request.env['mail.mass_mailing.contact'].sudo().search_count([('email', '=', email), ('list_id', '=', mailing_list.id)]) > 0,
            })
        return mailing_lists

    @http.route(['/my/mail', '/my/mail/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_mail(self, page=1, **post):
        #/my/mail?page=3
        mpp = 8 # mails per page
        home_user = request.env.user
        if home_user.has_group('webshop_dermanord.group_dn_sk'):
            return request.website.render('website.403', {})
        self.validate_user(home_user)
        values = self._prepare_portal_layout_values()
        email = request.env.user.email
        mailing_lists = self.get_mailing_lists(email)
        _logger.warn("%s haze" %mailing_lists)
        mass_mailing_partners =[mmc['id'] for mmc in request.env['mail.mass_mailing.contact'].sudo().search_read([('email', '=', email)], ['id'])]
        mail_count = request.env['mail.mail.statistics'].sudo().search_count([('model', '=', 'mail.mass_mailing.contact'), ('res_id', 'in', mass_mailing_partners)])
        page_count = int(ceil(mail_count / mpp))
        pager = request.website.pager(
            url="/my/mail",
            total=mail_count,
            page=page,
            step=10,
        )

        employees_mailing_lists = {}
        employees = request.env['res.partner'].search([('parent_id', '=', home_user.commercial_partner_id.id), ('type', '=', 'contact'), ('email', '!=', False), ('id', '!=', home_user.partner_id.id)])

        for employee in employees:
            employees_mailing_lists[employee.id] = self.get_mailing_lists(employee.email)
        mails = request.env['mail.mail.statistics'].sudo().search([('model', '=', 'mail.mass_mailing.contact'), ('res_id', 'in', mass_mailing_partners)], limit=mpp, offset=pager['offset'], order='sent DESC')
        values.update({
            'home_user': home_user,
            'is_admin': self.check_admin_portal(home_user, request.env.user),
            'employees': employees,
            'mailing_lists': mailing_lists,
            'mass_mailing_partners': mass_mailing_partners,
            'mails': mails,
            'page_count': page_count,
            'pager': pager,
            'employees_mailing_lists': employees_mailing_lists,
            'active_menu': 'my_mail',
            })


        return request.render("website_portal_sale_1028.portal_my_mail", values)

    @http.route(['/my/mail/subscribe'], type='json', auth='user')
    def portal_my_mail_subscribe(self, subscribe=False, mailing_list_id=None, partner_id=None):
        """Subscribe / unsubscribe to a mailing list."""
        home_user = request.env.user
        self.validate_user(home_user)
        if partner_id:

            same_company = request.env['res.partner'].search_count([
                ('id', 'child_of', home_user.commercial_partner_id.id),
                ('id', '=', partner_id)
            ])
            if not same_company:
                raise AccessError('You are not allowed to administrate this user.')
            if partner_id != home_user.partner_id.id and not self.check_admin_portal(home_user):
                # Non-admin can only edit their own subscriptions
                raise AccessError('You need to be admin to administrate this user.')
            partner = request.env['res.partner'].sudo().browse(partner_id)
            email = partner.email
            name = partner.name
        else:
            email = request.env.user.email
            name = request.env.user.name
        try:
            mailing_list = request.env['mail.mass_mailing.list'].sudo().search([('website_published', '=', True), ('id', '=', mailing_list_id)])
            mailing_contact = request.env['mail.mass_mailing.contact'].sudo().search([('email', '=', email), ('list_id', '=', mailing_list.id)])
            if subscribe and not mailing_contact:
                request.env['mail.mass_mailing.contact'].sudo().create({
                    'email': email,
                    'name': name,
                    'list_id': mailing_list.id,
                    })
            elif subscribe and mailing_contact:
                # Check for duplicates and delete because why not
                done = False
                for contact in mailing_contact:
                    if done:
                        contact.unlink()
                        continue
                    done = True
                    if contact.opt_out:
                        contact.opt_out = False
            elif not subscribe and mailing_contact:
                mailing_contact.unlink()
            return True
        except:
            return False

    #Min salong

    @http.route(['/my/salon'], type='http', auth="user", website=True)
    def portal_my_salon(self, home_user=None, **post):
        home_user = request.env.user
        self.validate_user(home_user)
        company = home_user.partner_id.commercial_partner_id
        value = request.website.my_orders_get_data(home_user, post)
        value.update({
            'help': self.get_help(),
            'company_form': True,
            'contact_form': False,
            'address_types_readonly': self.get_address_types_readonly(),
            'invoice_type_selection': [(invoice_type['id'], invoice_type['name']) for invoice_type in request.env['sale_journal.invoice.type'].sudo().search_read([], ['name'])],
            'active_menu': 'my_salon',
        })
        value.update(self.get_children_by_address_type(company))
        return request.render("website_portal_sale_1028.portal_my_salon", value)

        # value.update(self.get_children_by_address_type(company))
        # # pages = [{'name': 'delivery', 'string': 'Delivery Address', 'type': 'contact_form', 'fields': [{'name': 'street1', 'string': 'Street', 'readonly': False, 'placeholder': 'Street 123'}...]}...]
        # return request.render('website_sale_home.home_page', value)

    def validate_user(self, user):
        """Check if logged in user is allowed to look at this account page."""
        if request.uid == request.env.ref('base.public_user').id:
            raise AccessError('You are not allowed to administrate this user.')
        if not user:
            raise AccessError('You are not allowed to administrate this user.')
        # All employees should be allowed to see all customers.
        if request.env.user.has_group('base.group_user'):
            return
        same_company = request.env['res.partner'].search_count([('id', 'child_of', request.env.user.commercial_partner_id.id), ('id', '=', user.partner_id.id)])
        if not same_company:
            raise AccessError('You are not allowed to administrate this user.')

    def update_info(self, home_user, post):
        if not self.check_admin_portal(home_user):
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

            address_types = self.get_children_by_address_type(company)
            if len(address_types['delivery']) == 0:
                # Create new delivery address if email is updated
                # without an existing delivery address
                if post.get('delivery_email'):
                    delivery_params = {
                        'name': 'delivery',
                        'parent_id': company.id,
                        'use_parent_address': True,
                        'email': post.get('delivery_email'),
                        'type': 'delivery',
                    }
                    request.env['res.partner'].sudo().create(delivery_params)

            elif len(address_types['delivery']) == 1:
                # Update email for delivery address if only one
                if post.get('delivery_email'):
                    address_types['delivery'].email = post.get('delivery_email')
            else:
                # Update email for each delivery address if several
                for deliv in address_types['delivery']:
                    if post.get('delivery_id%s_email' % deliv.id):
                        deliv.email = post.get('delivery_id%s_email' % deliv.id)

            company.write(self.get_company_post(post))
            children_dict = self.save_children(company, post)
            children = children_dict['children']
            validation = children_dict['validations']
            for field in self.company_fields():
                validation['company_%s' %field] = 'has-success'


    def get_help(self):
        help = {}
        help['help_company_name'] = _('')
        help['help_delivery_street'] = _('')
        help['help_delivery_street2'] = _('')
        help['help_delivery_zip'] = _('')
        help['help_delivery_city'] = _('')
        help['help_delivery_phone'] = _('')
        help['help_delivery_email'] = _('This e-mail will be used to send tracking information of orders.')
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
        help['help_social_media_facebook'] = _('')
        help['help_social_media_instagram'] = _('')
        help['help_social_media_youtube'] = _('')
        help['help_social_media_twitter'] = _('')
        return help

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
        return ['delivery', 'invoice']

    # can be overridden with more address type
    def get_children_by_address_type(self, company):
        return {
            'delivery': company.child_ids.filtered(lambda c: c.type == 'delivery'),
            'invoice': company.child_ids.filtered(lambda c: c.type == 'invoice'),
        }

    # can be overridden with more address type
    def save_children(self, partner_id, post):
        address_type = set(self.get_address_type()) - set(self.get_address_types_readonly())
        _logger.warn('sandra %s %s %s' % (address_type, self.get_address_type(), self.get_address_types_readonly()))
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
        # ~ _logger.warn(post)
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
            # ~ _logger.warn('child_dict\n%s' % child_dict)
            if address_type != 'contact':
                child_dict['name'] = address_type
            child_dict['type'] = address_type
            child_dict['use_parent_address'] = False
            if child_dict.get('country_id'):
                child_dict['country_id'] = int(child_dict['country_id'])
            child = partner_id.child_ids.filtered(lambda c: c.type == address_type)
            if not child:
                child_dict['parent_id'] = partner_id.id
                child = request.env['res.partner'].sudo().create(child_dict)
            else:
                child[0].write(child_dict)
            for field in PARTNER_FIELDS:
                validation['%s_%s' %(address_type, field)] = 'has-success'
            res['child'] |= child
        # ~ _logger.warn(child_dicts)
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

            # update company info
    @http.route(['/my/salon/<model("res.users"):home_user>/info_update'], type='http', auth="user", website=True)
    def info_update(self, home_user=None, **post):
        # update data for main partner
        self.validate_user(home_user)
        if not self.check_admin_portal(home_user):
            return request.website.render('website.403', {})
        if home_user == request.env.user:
            home_user = home_user.sudo()
        self.update_info(home_user, post)
        return werkzeug.utils.redirect("/my/salon")

    @http.route(['/my/salon/<model("res.users"):home_user>/add_tags'], type='http', auth="user", website=True)
    def add_tags(self, home_user=None, **post):
        self.validate_user(home_user)
        if home_user == request.env.user:
            home_user = home_user.sudo()
        if not self.check_admin_portal(home_user):
            return request.website.render('website.403', {})

        tag = request.env.ref('website_portal_sale_1028.partner_tag_delete')
        home_user.category_id |= tag

        return request.render("website_portal_sale_1028.portal_my_tags")

    def create_contact_user_portal(self, values):
        template = request.env.ref('website_portal_sale_1028.contact_template2').sudo()
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


    @http.route(['/my/orders/<int:order_id>'], type='http', auth="user", website=True)
    def orders_followup(self, home_user=None, order_id=None, tab='orders', **post):
        home_user = request.env.user
        self.validate_user(home_user)
        order = request.env['sale.order'].sudo().search(request.website.my_order_search_domain(home_user, post=post) + [('id', '=', order_id)])
        if not order:
            html = request.website._render(
                    'website.403',
                    {
                        'status_code': 403,
                        'status_message': werkzeug.http.HTTP_STATUS_CODES[403]
                    })
            return werkzeug.wrappers.Response(html, status=403, content_type='text/html;charset=utf-8')

        return request.render("website_portal_sale_1028.orders_followup", {
            'home_user': request.env.user,
            'order': order,
            'tab': tab,
        })

    @http.route(['/my/orders/<model("res.users"):home_user>/order/<model("sale.order"):order>/copy',], type='http', auth="user", website=True)
    def my_order_copy(self, home_user=None, order=None, **post):
        self.validate_user(home_user)
        sale_order = request.website.sale_get_order()
        if not sale_order:
            sale_order = request.website.sale_get_order(force_create=True)
        order_lines = request.env['sale.order.line']
        try:
            for line in order.sudo().order_line.filtered(lambda l: not (l.event_id or l.sudo().product_id.event_ok) and l.product_id.active == True and l.product_id.sale_ok == True and l.product_id.website_published == True):
                # Check access rights
                try:
                    order_lines += order_lines.browse(line.id)
                except:
                    pass # Probably access error.
        except Exception as e:
            order_lines = []
            _logger.warn('Order Copy Error %s' % e)

        for line in order_lines:
            if line.sale_home_confirm_copy():
                request.env['sale.order.line'].sudo().create({
                        'order_id': sale_order.id,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_uom_qty,
                })
        return werkzeug.utils.redirect("/shop/cart")

    def check_document_access(self, ids, report=None):
        partner = request.env.user.commercial_partner_id
        model = None
        if report == 'sale.report_saleorder':
            model = 'sale.order'
        elif report == 'account.report_invoice':
            model = 'account.invoice'
        elif report == 'stock_delivery_slip.stock_delivery_slip':
            model = 'stock.picking'
        if model:
            try:
                # Check partner_id.
                if not (set(ids) - set([r['id'] for r in request.env[model].sudo().search_read([('partner_id', 'child_of', partner.id)], ['id'])])):
                    return True
                # Check ordinary access controls
                records = request.env[model].browse(ids)
                records.check_access_rights('read')
                records.check_access_rule('read')
                return True
            except:
                # This check failed. Let it go to super to perform other checks.
                pass
        return super(website_account, self).check_document_access(ids, report=report)

        # new contact, update contact
    @http.route(['/my/salon/<model("res.users"):home_user>/contact/new', '/my/salon/<model("res.users"):home_user>/contact/<model("res.partner"):partner>'], type='http', auth='user', website=True)
    def contact_page(self, home_user=None, partner=None, **post):
        self.validate_user(home_user)
        validation = {}
        help_dic = self.get_help()
        company = home_user.partner_id.commercial_partner_id
        if partner:
            # Why?
            if not (partner in company.child_ids):
                partner = request.env['res.partner'].sudo().browse([])

        value = request.website.my_orders_get_data(home_user, post)
        #~ _logger.warn(value)
        values = {}
        if request.httprequest.method == 'POST':
            if not self.check_admin_portal(home_user):
                return request.website.render('website.403', {})
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
                        user = self.create_contact_user_portal(values)
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
                return werkzeug.utils.redirect('/my/salon/%s/contact/%s' % (home_user.id, partner and partner.id or 'new'))
        value.update({
            'help': help_dic,
            'contact': partner,
            'validation': validation,
            'contact_values': values,
            'company_form': False,
            'contact_form': True,
            'access_warning': '',
            'mailing_lists': partner and self.get_mailing_lists(partner.email) or [],
        })
        return request.render('website_portal_sale_1028.contact_form', value)

    def details_form_validate(self, data):
        error, error_message = super(website_account, self).details_form_validate(data)
        # prevent VAT/name change if invoices exist
        partner = request.env['res.users'].browse(request.uid).partner_id
        invoices = request.env['account.invoice'].sudo().search_count([('partner_id', '=', partner.id), ('state', 'not in', ['draft', 'cancel'])])
        if invoices:
            if 'vat' in data and (data['vat'] or False) != (partner.vat or False):
                error['vat'] = 'error'
                error_message.append(_('Changing VAT number is not allowed once invoices have been issued for your account. Please contact us directly for this operation.'))
            if 'name' in data and (data['name'] or False) != (partner.name or False):
                error['name'] = 'error'
                error_message.append(_('Changing your name is not allowed once invoices have been issued for your account. Please contact us directly for this operation.'))
        return error, error_message


    def check_admin_portal(self, home_user, user=False):
        """Check if the active user is allowed to administrate this account."""
        user = user or request.env.user
        if user.partner_id.commercial_partner_id != home_user.commercial_partner_id:
            return False
        if not user.has_group('website_portal_sale_1028.group_portal_admin'):
            return False
        return True

    @http.route(['/my/salon/send_message'], type='json', auth="user", website=True)
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
            if not self.check_admin_portal(home_user, user):
                return request.website.render('website.403', {})
            else:
                user.active = False
        body = _("""%s wants to delete <a href="/web?debug=#id=%s&view_type=form&model=res.partner">%s</a> because '%s'.""") % (request.env.user.name, partner.id, partner.name, reason)
        subject = _("Contact %s inactivated") % partner.name
        partner.commercial_partner_id.message_post(body=body, subject=subject)
        partner.message_post(body=body, subject=subject)
        partner.active = False

    # delete contact
    @http.route(['/my/salon/<model("res.users"):home_user>/contact/<model("res.partner"):partner>/delete'], type='http', method="post", auth='user', website=True)
    def contact_delete(self, home_user=None, partner=None, **post):
        #~ home_user = request.env['res.users'].browse(post.get('home_user'))
        #~ partner = request.env['res.partner'].browse(post.get('partner_id'))
        reason = post.get('reason', '')
        company = home_user.partner_id.commercial_partner_id
        if not self.check_admin_portal(home_user):
            return request.website.render('website.403', {})
        if partner and partner in company.child_ids:
            try:
                self.delete_contact(home_user, partner, reason)
            except AccessError:
                return request.website.render('website.403', {})
        return werkzeug.utils.redirect('/my/salon/%s' % home_user.id)

    # send reset password to contact
    @http.route(['/my/salon/contact/pw_reset'], type='json', auth='user', website=True)
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
    @http.route(['/my/salon/contact/remove_img_contact'], type='json', auth="public", website=True)
    def contact_remove_img(self, partner_id='0', **kw):
        partner = request.env['res.partner'].browse(int(partner_id))
        if partner:
            partner.write({'image': None})
            return True
        return False

    # delete contact attachment
    @http.route(['/my/salon/<model("res.users"):home_user>/attachment/<int:attachment>/delete'], type='http', auth='user', website=True)
    def contact_attachment_delete_portal(self, home_user=None, attachment=0, **post):
        if not self.check_admin_portal(home_user):
            return request.website.render('website.403', {})
        company = home_user.partner_id.commercial_partner_id
        if attachment > 0:
            attachment = request.env['ir.attachment'].sudo().browse(attachment)
            if attachment.res_model == 'res.partner' and attachment.res_id != 0:
                partner = request.env['res.partner'].browse(attachment.res_id)
                if partner.parent_id == home_user.partner_id.commercial_partner_id:
                    attachment.unlink()
        return werkzeug.utils.redirect('/my/salon/%s/contact/%s' % (home_user.id, partner.id))

class DummyRecordSet(object):
    def __init__(self, ids):
        self.ids = ids

class MailMassMailingList(models.Model):
    _inherit = 'mail.mass_mailing.list'

    country_ids = fields.Many2many(comodel_name='res.country',string='Country')

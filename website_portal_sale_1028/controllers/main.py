# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import http, _
from openerp.exceptions import AccessError
from openerp.http import request

from openerp.addons.website_portal_1028.controllers.main import website_account

import logging
_logger = logging.getLogger(__name__)

class website_account(website_account):

    @http.route()
    def account(self, **kw):
        """ Add sales documents to main account page """
        response = super(website_account, self).account(**kw)
        partner = request.env.user.partner_id

        SaleOrder = request.env['sale.order']
        Invoice = request.env['account.invoice']
        quotation_count = SaleOrder.search_count([
            ('message_follower_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['sent', 'cancel'])
        ])
        order_count = SaleOrder.search_count([
            ('message_follower_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['sale', 'done'])
        ])
        invoice_count = Invoice.search_count([
            ('type', 'in', ['out_invoice', 'out_refund']),
            ('message_follower_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['open', 'paid', 'cancel'])
        ])

        response.qcontext.update({
            'quotation_count': quotation_count,
            'order_count': order_count,
            'invoice_count': invoice_count,
        })
        return response

    #
    # Quotations and Sale Orders
    #

    # @http.route(['/my/quotes', '/my/quotes/page/<int:page>'], type='http', auth="user", website=True)
    # def portal_my_quotes(self, page=1, date_begin=None, date_end=None, **kw):
    #     values = self._prepare_portal_layout_values()
    #     partner = request.env.user.partner_id
    #     SaleOrder = request.env['sale.order']

    #     domain = [
    #         ('message_follower_ids', 'child_of', [partner.commercial_partner_id.id]),
    #         ('state', 'in', ['sent', 'cancel'])
    #     ]

    #     # archive_groups = self._get_archive_groups('sale.order', domain)
    #     archive_groups = "" # DAER: Ugg not understand, Ugg remove.
    #     if date_begin and date_end:
    #         domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

    #     # count for pager
    #     quotation_count = SaleOrder.search_count(domain)
    #     # make pager
    #     pager = request.website.pager(
    #         url="/my/quotes",
    #         url_args={'date_begin': date_begin, 'date_end': date_end},
    #         total=quotation_count,
    #         page=page,
    #         step=self._items_per_page
    #     )
    #     # search the count to display, according to the pager data
    #     quotations = SaleOrder.search(domain, limit=self._items_per_page, offset=pager['offset'])

    #     values.update({
    #         'date': date_begin,
    #         'quotations': quotations,
    #         'pager': pager,
    #         'archive_groups': archive_groups,
    #         'default_url': '/my/quotes',
    #     })
    #     return request.render("website_portal_sale_1028.portal_my_quotations", values)

    @http.route(['/my/orders', '/my/orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_orders(self, page=1, date_begin=None, date_end=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        SaleOrder = request.env['sale.order']

        domain = [
            ('message_follower_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['sale', 'done'])
        ]
        archive_groups = "" # DAER: Ugg not understand, Ugg remove.
        # archive_groups = self._get_archive_groups('sale.order', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # count for pager
        order_count = SaleOrder.search_count(domain)
        # pager
        pager = request.website.pager(
            url="/my/orders",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=order_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        orders = SaleOrder.search(domain, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'date': date_begin,
            'orders': orders,
            'page_name': 'order',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/orders',
        })
        return request.render("website_portal_sale_1028.portal_my_orders", values)

    @http.route(['/my/media'], type='http', auth="user", website=True)
    def portal_my_media(self, **kw):
        values = self._prepare_portal_layout_values()
        return request.render("website_portal_sale_1028.portal_my_media", values)

    @http.route(['/my/buyinfo'], type='http', auth="user", website=True)
    def portal_my_buy_info(self, **kw):
        values = self._prepare_portal_layout_values()
        return request.render("website_portal_sale_1028.portal_my_buy_info", values)

    @http.route(['/my/obsolete'], type='http', auth="user", website=True)
    def portal_my_obsolete(self, **kw):
        values = self._prepare_portal_layout_values()
        return request.render("website_portal_sale_1028.portal_my_obsolete", values)

    @http.route(['/my/salon'], type='http', auth="user", website=True)
    def portal_my_salon(self, **kw):
        values = self._prepare_portal_layout_values()
        return request.render("website_portal_sale_1028.portal_my_salon", values)

    @http.route(['/my/orders/<int:order>'], type='http', auth="user", website=True)
    def orders_followup(self, order=None, **kw):
        order = request.env['sale.order'].browse([order])
        try:
            order.check_access_rights('read')
            order.check_access_rule('read')
        except AccessError:
            return request.render("website.403")

        order_sudo = order.sudo()
        order_invoice_lines = {il.product_id.id: il.invoice_id for il in order_sudo.invoice_ids.mapped('invoice_line')}

        return request.render("website_portal_sale_1028.orders_followup", {
            'order': order_sudo,
            'order_invoice_lines': order_invoice_lines,
        })

    #
    # Invoices
    #

    # @http.route(['/my/invoices', '/my/invoices/page/<int:page>'], type='http', auth="user", website=True)
    # def portal_my_invoices(self, page=1, date_begin=None, date_end=None, **kw):
    #     values = self._prepare_portal_layout_values()
    #     partner = request.env.user.partner_id
    #     AccountInvoice = request.env['account.invoice']

    #     domain = [
    #         ('type', 'in', ['out_invoice', 'out_refund']),
    #         ('message_follower_ids', 'child_of', [partner.commercial_partner_id.id]),
    #         ('state', 'in', ['open', 'paid', 'cancel'])
    #     ]
    #     archive_groups = "" # DAER: Ugg not understand, Ugg remove.
    #     # archive_groups = self._get_archive_groups('account.invoice', domain)
    #     if date_begin and date_end:
    #         domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

    #     # count for pager
    #     invoice_count = AccountInvoice.search_count(domain)
    #     # pager
    #     pager = request.website.pager(
    #         url="/my/invoices",
    #         url_args={'date_begin': date_begin, 'date_end': date_end},
    #         total=invoice_count,
    #         page=page,
    #         step=self._items_per_page
    #     )
    #     # content according to pager and archive selected
    #     invoices = AccountInvoice.search(domain, limit=self._items_per_page, offset=pager['offset'])
    #     values.update({
    #         'date': date_begin,
    #         'invoices': invoices,
    #         'page_name': 'invoice',
    #         'pager': pager,
    #         'archive_groups': archive_groups,
    #         'default_url': '/my/invoices',
    #     })
    #     return request.render("website_portal_sale_1028.portal_my_invoices", values)

    # @http.route(['/my/invoices/pdf/<int:invoice_id>'], type='http', auth="user", website=True)
    # def portal_get_invoice(self, invoice_id=None, **kw):
    #     invoice = request.env['account.invoice'].browse([invoice_id])
    #     try:
    #         invoice.check_access_rights('read')
    #         invoice.check_access_rule('read')
    #     except AccessError:
    #         return request.render("website.403")

    #     pdf = request.env['report'].sudo().get_pdf([invoice_id], 'account.report_invoice')
    #     pdfhttpheaders = [
    #         ('Content-Type', 'application/pdf'), ('Content-Length', len(pdf)),
    #         ('Content-Disposition', 'attachment; filename=Invoice.pdf;')
    #     ]
    #     return request.make_response(pdf, headers=pdfhttpheaders)

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

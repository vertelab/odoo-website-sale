# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import api, exceptions, models
import math

class website(models.Model):
    _inherit="website"

    @api.model
    def sale_home_get_data(self, home_user, post):
        res = super(website, self).sale_home_get_data(home_user, post)
        res.update(self.sale_home_order_get(home_user, post))
        filters = self.sale_home_order_get_all_filters(home_user)
        for filter in filters:
            if post.get(filter['id']):
                filter['active'] = True
        res['order_filters'] = filters
        return res

    @api.model
    def sale_home_order_get_all_filters(self, user):
        return []
    
    @api.model
    def sale_home_order_filter_domain(self, user, filter, value):
        """Override to implement filters."""
        return []
    
    @api.model
    def sale_home_order_search_domain_access(self, user, search):
        """Return a domain that describes which sale orders the user has access to."""
        return [('partner_id','child_of', user.partner_id.commercial_partner_id.id), ('state','!=','draft')]

    @api.model
    def sale_home_order_search_domain(self, user, search=None, post=None):
        domain = self.sale_home_order_search_domain_access(user, search)
        # ~ _logger.warn('\n\ndomain: %s\n' % domain)
        post = post or {}

        if search:
            search = search.strip()
            # invoices and picking
            orders = self.env['sale.order'].sudo().search_read(domain, ['invoice_ids', 'picking_ids'])
            # ~ _logger.warn('\n\norders: %s\n' % orders)
            invoice_ids = set()
            picking_ids = set()
            for o in orders:
                invoice_ids |= set(o['invoice_ids'] or [])
                picking_ids |= set(o['picking_ids'] or [])
            # ~ _logger.warn('\ninvoice_ids: %s\npicking_ids: %s' % (invoice_ids, picking_ids))
            # TODO: Date search only works with ISO-format. Find better implementation.
            invoice_ids = [d['id'] for d in self.env['account.invoice'].sudo().search_read([
                    ('id', 'in', list(invoice_ids)),
                    '|',
                        '|',
                            ('name', 'ilike', search),
                            ('number', 'ilike', search),
                        ('date_invoice', 'ilike', search)
                ], ['id'])]
            picking_ids = self.env['stock.picking'].sudo().search_read([('id', 'in', list(picking_ids)), ('name', 'ilike', search)], ['group_id'])
            # ~ _logger.warn('\n\ninvoice_ids: %s\n' % invoice_ids)
            # ~ _logger.warn('\n\npicking_ids: %s\ngroup_ids: %s\n' % (picking_ids, [d['group_id'][0] for d in picking_ids if d['group_id']]))
            domain += ['|', '|', '|', '|', '|',
                        ('invoice_ids', 'in', invoice_ids),
                        ('procurement_group_id', 'in', [d['group_id'][0] for d in picking_ids if d['group_id']]),
                        ('name', 'ilike', search),
                        ('date_order', 'ilike', search),
                        ('client_order_ref', 'ilike', search),
                        ('user_id', 'ilike', search)]
        for key in post:
            if key.startswith('order_filter_'):
                domain += self.sale_home_order_filter_domain(user, key, post[key])
        # ~ _logger.debug('search_domain: %s' % (domain))
        return domain

    @api.model
    def sale_home_order_get(self, user, post):
        OPP = 50 # Orders Per Page
        search = post.get('order_search')
        domain = self.sale_home_order_search_domain(user, search, post)
        order_page = int(post.get('order_page', '1'))
        url_args = post.copy()
        url_args.update({
            'order_page': '__ORDER_PAGE__',
            'tab': 'orders',
        })
        pager = self.pager(url='/home/%s' % user.id, total=self.env['sale.order'].sudo().search_count(domain), page=order_page, step=OPP, scope=7, url_args=url_args)
        for page in pager["pages"]:
            page['url'] = page['url'].replace('/page/%s' % page['num'], '').replace('__ORDER_PAGE__', str(page['num']))
        for page in ["page", "page_start", "page_previous", "page_next", "page_end"]:
            pager[page]['url'] = pager[page]['url'].replace('/page/%s' % pager[page]['num'], '').replace('__ORDER_PAGE__', str(pager[page]['num']))
        return {
            'sale_orders': self.env['sale.order'].sudo().search(domain, limit=OPP, offset=(order_page - 1) * OPP),
            'sale_order_pager': pager,
            'order_search': search,
        }

    @api.model
    def sale_home_order_get_invoice(self, order):
        invoice = order.invoice_ids[-1] if order and order.invoice_ids else None
        if invoice:
            document = self.env['ir.attachment'].search([('res_id', '=', invoice.id), ('res_model', '=', 'account.invoice')]).mapped('id')
            if document:
                return ('/attachment/%s/invoice.pdf' % document[-1], invoice.number, invoice.state)
            return ('', invoice.number, invoice.state)
        else:
            return ('', 'in progress...', '')


    def sale_home_order_get_picking(self, order):
        picking = order.picking_ids[-1] if order and order.picking_ids else None
        if picking:
            return ('/report/pdf/stock_delivery_slip.stock_delivery_slip/%s' % picking.id, picking.name, picking.state)
        else:
            return ('', 'in progress...', '')


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.multi
    def get_access_action(self):
        """ Instead of the classic form view, redirect to the online quote for
        portal users that have access to a confirmed order. """
        # TDE note: read access on sale order to portal users granted to followed sale orders
        self.ensure_one()
        if self.state == 'cancel' or (self.state == 'draft' and not self.env.context.get('mark_so_as_sent')):
            return super(SaleOrder, self).get_access_action()
        if self.env.user.share or self.env.context.get('force_website'):
            try:
                self.check_access_rule('read')
            except exceptions.AccessError:
                pass
            else:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/my/orders/%s' % self.id,
                    'target': 'self',
                    'res_id': self.id,
                }
        return super(SaleOrder, self).get_access_action()

    @api.multi
    def _notification_recipients(self, message, groups):
        groups = super(SaleOrder, self)._notification_recipients(message, groups)

        self.ensure_one()
        if self.state not in ('draft', 'cancel'):
            for group_name, group_method, group_data in groups:
                group_data['has_button_access'] = True

        return groups

    def _force_lines_to_invoice_policy_order(self):
        for line in self.order_line:
            if self.state in ['sale', 'done']:
                line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    def check_document_access(self, report, ids):
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
                records = request.env[model].browse(ids)
                # Check partner_id.
                if all([r.partner_id.commercial_partner_id == partner for r in records.sudo()]):
                    return True
                # Check ordinary access controls
                records.check_access_rights('read')
                records.check_access_rule('read')
                return True
            except:
                # This check failed. Let it go to super to perform other checks.
                pass
        return super(website_sale_home, self).check_document_access(report, ids)


# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import api, exceptions, models, fields

class knowledge_config_settings(models.TransientModel):
    _inherit = 'knowledge.config.settings'

    document_directory = fields.Char(string='Document Directory Domain', help='Specify the document directory domain')

    @api.one
    def set_params(self):
        self.env['ir.config_parameter'].set_param('website_portal_sale_1028.document_directory', self.document_directory)

    @api.model
    def get_params(self, fields):
        return {'document_directory': self.env['ir.config_parameter'].get_param('website_portal_sale_1028.document_directory')}


class website(models.Model):
    _inherit="website"

    @api.model
    def portal_sale_document_get(self, user, domain):
        if not domain:
            domain = "[('parent_id.name', '=', 'Public')]"
        return self.env['ir.attachment'].sudo().search(eval(domain))

    @api.model
    def portal_sale_document_type_get(self, doc):
        suffix = ''
        mime_to_type = {'application/pdf': 'pdf',
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
                        'application/vnd.ms-excel': 'xls',
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
                        'application/vnd.ms-office': 'xlm',
                        }

        suffix = mime_to_type.get(doc.mimetype)
        if not suffix: 
            suffix = mime_to_type.get(doc.file_type)
        if not suffix:
            if 'PDF' in doc.name:
                suffix = 'pdf'
            elif 'Excel' in doc.name:
                suffix = 'xls'
        _logger.warn(suffix)
        return (('/%s' % doc.id) + '.' + suffix) if suffix else ''

    @api.model
    def portal_sale_directory_get(self, user):
        return self.env['document.directory'].sudo().search([('name', '=', 'public')])

    @api.model
    def my_order_get_all_filters(self, user):
        # /odoo-website-sale/website_sale_home_order/website_sale.py sale_home_order_get_all_filters
        return []
    
    @api.model
    def my_order_filter_domain(self, user, filter, value):
        """Override to implement filters."""
        # /odoo-website-sale/website_sale_home_order/website_sale.py sale_home_order_filter_domain
        return []
    
    @api.model
    def my_order_search_domain_access(self, user, search):
        """Return a domain that describes which sale orders the user has access to."""
        # /odoo-website-sale/website_sale_home_order/website_sale.py sale_home_order_search_domain_access
        return [('partner_id','child_of', user.partner_id.commercial_partner_id.id), ('state','!=','draft')]

    @api.model
    def my_order_search_domain(self, user, search=None, post=None):
        # /odoo-website-sale/website_sale_home_order/website_sale.py sale_home_order_search_domain
        domain = self.my_order_search_domain_access(user, search)
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
                domain += self.my_order_filter_domain(user, key, post[key])
        return domain

    @api.model
    def my_order_get_invoice(self, order):
        invoice = order.invoice_ids[-1] if order and order.invoice_ids else None
        if invoice:
            document = self.env['ir.attachment'].search([('res_id', '=', invoice.id), ('res_model', '=', 'account.invoice')]).mapped('id')
            if document:
                return ('/attachment/%s/invoice.pdf' % document[-1], invoice.number, invoice.state)
            return ('', invoice.number, invoice.state)
        else:
            return ('', 'in progress...', '')

    def my_order_get_picking(self, order):
        picking = order.picking_ids[-1] if order and order.picking_ids else None
        if picking:
            return ('/report/pdf/stock_delivery_slip.stock_delivery_slip/%s' % picking.id, picking.name, picking.state)
        else:
            return ('', 'in progress...', '')

    def get_portal_documents(self, doc_type):
        #cat_public = self.env.ref('website_portal_sale_1028.catalog_pricelists')
        catalog = None
        if doc_type == 'event':
            catalog = self.env.ref('website_portal_sale_1028.catalog_event')  
        if doc_type == 'news':
            catalog = self.env.ref('website_portal_sale_1028.catalog_news')
        if doc_type == 'compendium':
            catalog = self.env.ref('website_portal_sale_1028.catalog_compendium')
        if doc_type == 'other':
            catalog = self.env.ref('website_portal_sale_1028.catalog_other')
        
        if catalog:
            return self.env['ir.attachment'].sudo().search([('parent_id', '=', catalog.id)])
        # return []


    # def get_portal_documents_news(self, doc_type):
    #     #cat_public = self.env.ref('website_portal_sale_1028.catalog_pricelists')
    #     catalog_news = None
    #     if doc_type == 'news':
    #         catalog_news = self.env.ref('website_portal_sale_1028.catalog_news')
        
    #     if catalog_news:
    #         return self.env['ir.attachment'].sudo().search([('parent_id', '=', catalog_news.id)])
    #     return []

    @api.model
    def my_orders_get_data(self, home_user, post):
        return {
            'home_user': home_user,
            'tab': post.get('tab', 'settings'),
            'validation': {},
            'country_selection': [(country['id'], country['name']) for country in self.env['res.country'].search_read([], ['name'])],
            'default_country': (home_user and home_user.country_id and home_user.country_id.id) or (self.company_id and self.company_id.country_id and self.company_id.country_id.id),
        }

    @api.model
    def my_orders_access_control(self, home_user):
        def check_admin_portal(home_user):
            if self.env.user.partner_id.commercial_partner_id != home_user.commercial_partner_id:
                return False
            if self.env.ref('website_portal_sale_1028.group_portal_admin') not in self.env.user.groups_id:
                return False
            return True
        if not check_admin_portal(home_user):
            company_admin = []
            for contact in home_user.partner_id.commercial_partner_id.child_ids.filtered(lambda c: c.type == 'contact'):
                if self.env['res.users'].search([('partner_id', '=', contact.id)]):
                    if self.env.ref('website_portal_sale_1028.group_portal_admin') in self.env['res.users'].search([('partner_id', '=', contact.id)]).groups_id:
                        company_admin.append(contact.name)
            if len(company_admin) > 0:
                return ('You have not access right to edit or create contact for your company. Please contact your administrator: %s.' % ' or '.join(a for a in company_admin))
            else:
                return ('You have not access right to edit or create contact for your company. Please contact us.')
        return ''

class MassMailingList(models.Model):
    _inherit = 'mail.mass_mailing.list'

    website_published = fields.Boolean(string='Published')




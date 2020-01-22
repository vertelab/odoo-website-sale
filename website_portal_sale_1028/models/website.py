# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import api, exceptions, models, fields


class website(models.Model):
    _inherit="website"

    def get_portal_documents(self, doc_type):
        #cat_public = self.env.ref('website_portal_Sale_1028.catalog_pricelists')
        catalog = None
        if doc_type == 'pricelists':
            catalog = self.env.ref('website_portal_Sale_1028.catalog_pricelists')
        
        if catalog:
            return self.env['ir.attachment'].sudo().search([('parent_id', '=', catalog.id)])
        return []

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

class MassMailingList(models.Model):
    _inherit = 'mail.mass_mailing.list'

    website_published = fields.Boolean(string='Published')




# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2018 Vertel (<http://vertel.se>).
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


import logging
_logger = logging.getLogger(__name__)

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning

import requests
from requests.auth import HTTPBasicAuth
import json
import sys, traceback

class WikinggruppenAPI84(object):
    WKG_CLASSES = ['Article', 'Category', 'Customer', 'Front', 'NewsletterRecipient', 'Order', 'OrderStatus', 'PriceList', 'ProductImage', 'ShippingMethod', 'Stock']
    WKG_FUNCTIONS = {
        'Article': ['get', 'create', 'update'],
        'Category': ['get', 'create', 'update'],
        'Customer': ['get', 'create', 'update'],
        'Front': ['get'],
        'NewsletterRecipient': ['get', 'create', 'update', 'delete'],
        'Order': ['get', 'create', 'update', 'cancel', 'restore'],
        'OrderStatus': ['get', 'create', 'update'],
        'PriceList': ['get', 'create', 'update', 'delete'],
        'ProductImage': ['get', 'create', 'delete'],
        'ShippingMethod': ['get'],
        'Stock': ['get', 'update'],
    }
    WKG_TRANS = {
        'Article': [
            'title',
            'description',
            'metaTitle',
            'metaDescription',
            'h1',
            'customText',
            'emptyStockText',
        ],
    }
    WKG_CURRENCY = {
        'Article': [
            'price',
            'campaignPrice',
        ],
    }
    
    def __init__(self, env):
        self.env = env
    
    def wkg_function(self, method, params):
        """Perform a WGR API function."""
        data = {'jsonrpc': '2.0', 'method': method, 'params': params}
        username = self.env['ir.config_parameter'].get_param('wikinggruppen.api_key')
        password = self.env['ir.config_parameter'].get_param('wikinggruppen.passwd')
        url = self.env['ir.config_parameter'].get_param('wikinggruppen.url')
        json_data = {}
        try:
            response = requests.post(
                url,
                json=data,
                auth=HTTPBasicAuth(username, password))
            json_data = response.json()
        except:
            e = sys.exc_info()
            tb = ''.join(traceback.format_exception(e[0], e[1], e[2]))
            _logger.warn("Connection to WGR Failed!\nmethod: %s\nparams: %s\n%s" % (method, params, tb))
            raise Warning(_("Connection to WGR Failed!") + "\nmethod: %s\nparams: %s" % (method, params))
        if not 'result' in json_data:
            _logger.warn("Connection to WGR Failed!\nstatus_code: %s\nmethod: %s\nerror: %s\nparams: %s\njson_data: %s" % (response.status_code, method, json_data.get('error'), params, json_data))
            raise Warning(_("Connection to WGR Failed!") + "\nstatus_code: %s\nmethod: %s\nmessage: %s\nparams: %s" % (response.status_code, method, json_data.get('error', {}).get('message'), params))
        return json_data.get('result')
    
    def article_get(self, id=None, article_nr=None):
        """Search for products.
        https://api.wikinggruppen.se/docs/8.4.0/#article-get
        Request parameters	

        If no parameters are given, all articles will be returned.
        Parameter 	    Type 	    Description
        updatedFrom 	DateTime 	Date and time when the article was updated (YYYY-MM-DD HH:MM:SS)
        articleNumber 	string 	    Article number
        id 	            integer		Article id (variant level)
        productId 	    integer		Article id (product level)
        stockPlace 	    string		Name of the physical place where the article is stored
        EANCode 	    string		EAN code (when using a scanner)
        categoryId 	    integer		Category which the article is connected to
        frontId 	    integer		Front which the article is connected to
        getURLs 	    boolean		Include all URLs to the product (URLs in default category per language and front)
        getImages 	    boolean		Include meta-data about images (no binary data)"""
        data = {}
        if id:
            data['id'] = id
        elif article_nr:
            data['articleNumber'] = article_nr
        return self.wkg_function('Article.get', data)

# ~ class EnvironmentDummy(object):
    
    # ~ def __init__(self, api_key, passwd, url):
        # ~ self.values = {
            # ~ 'wikinggruppen.api_key': api_key,
            # ~ 'wikinggruppen.passwd': passwd,
            # ~ 'wikinggruppen.url': url,
        # ~ }
    
    # ~ def __getitem__(self, key):
        # ~ return self
    
    # ~ def get_param(self, key):
        # ~ return self.values.get(key)

# ~ env = EnvironmentDummy(api_key, passwd, url)
# ~ connector = WikinggruppenAPI84(env)
# ~ connector.article_get(article_nr='L-307942')

# ~ def count_occurences(l, field, duplicates_only=False):
    # ~ res = {}
    # ~ for d in l:
        # ~ if d[field] not in res:
            # ~ res[d[field]] = len(filter(lambda x: x[field] == d[field],  l))
    # ~ if duplicates_only:
        # ~ for key in res.keys():
            # ~ if res[key] < 2:
                # ~ del res[key]
    # ~ return sorted([(x, res[x]) for x in res], key=lambda x: x[1], reverse=True)

# ~ def get duplicates(l, field):
    

class Website(models.Model):
    _inherit = 'website'
        
    @api.model
    def wkg_get_connector(self):
        version = self.env['ir.config_parameter'].get_param('website_sale_wikinggruppen.api_version', '8.4')
        if version == '8.4':
            return WikinggruppenAPI84(self.env)
        raise Warning(_("Unsupported version of Wikinggruppen API!"))
    
    @api.model
    def wkg_get_languages(self):
        domain = [('code', '=like', '%s\\_%%' % l) for l in self.env['ir.config_parameter'].get_param('website_sale_wikinggruppen.languages', 'en,sv').split(',')]
        domain = [('active', '=', True)] + ['|' for i in range(len(domain) - 1)] + domain
        return self.env['res.lang'].search(domain)
    
    # ~ @api.model
    # ~ def wkg_str2html(self, inp):
        # ~ # Doesn't look like this is needed. Description fields are
        # ~ # automagically cleaned up on the WGR end. Comparisions between
        # ~ # Odoo and WGR values are tricky though, so we'll end up .
        # ~ mapping = {
            # ~ u'å': '&aring;',
            # ~ u'Å': '&Aring;',
            # ~ u'ä': '&auml;',
            # ~ u'Ä': '&Auml;',
            # ~ u'ö': '&ouml;',
            # ~ u'Ö': '&Ouml;',
        # ~ }
        # ~ for char in mapping:
            # ~ inp = inp.replace(char, mapping[char])
        # ~ return inp
    
    @api.model
    def wkg_get_pricelists(self, campaigns=True, per_field=True):
        res = {}
        domain = [('wkg_pricelist', '=', True)]
        if campaigns:
            domain.append(('wkg_campaign_pricelist', '=', True))
        pricelists = self.env['product.pricelist'].search(domain)
        if not per_field:
            for pricelist in pricelists:
                res[pricelist.currency_id.name] = pricelist
        else:
            for pricelist in pricelists:
                field = pricelist.wkg_campaign_pricelist and 'campaignPrice_%s' or 'price_%s'
                res[field % pricelist.currency_id.code] = pricelist
        return res

    @api.model
    def wkg_get_warehouse(self):
        return self.env['stock.warehouse'].browse(int(self.env['ir.config_parameter'].get_param('website_sale_wikinggruppen.warehouse_id', '1')))
    
    @api.model
    def wkg_get_taxes(self):
        taxes = {}
        for tax in self.env['account.tax'].browse([int(id) for id in self.env['ir.config_parameter'].get_param('website_sale_wikinggruppen.tax_ids', '').split(',')]):
            taxes[tax.amount] = tax
        return taxes

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'
    
    wkg_pricelist = fields.Boolean(string='WGR Pricelist', help="Checking this makes this a pricelist for Wikinggruppen. Only one pricelist per currency.")
    wkg_campaign_pricelist = fields.Boolean(string='WGR Campaign Pricelist', help="Checking this makes this a campaign pricelist for Wikinggruppen. Only one campaign pricelist per currency.")

class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'
    
    wkg_id = fields.Integer(string='WGR ID', help="The ID of this category in Wikinggruppen.")
    
    _sql_constraints = [('wkg_id_uniq', 'unique (wkg_id)', "The Wikinggruppen category must be unique.")]
    
    @api.multi
    def wkg_update_id(self, overwrite=False):
        """Try to match this category to the corresponding category in Wikinggruppen."""
        connector = self.env['website'].wkg_get_connector()
        lang = (self.env.context.get('lang') or self.env.user.lang).split('_')[0]
        remote_categs = connector.wkg_function('Category.get', {})
        wgr_top_category = self.env.ref('website_sale_wikinggruppen.wgr_top_category')
        # Filtering is specific to KR. Special Brand categories.
        if self._name == 'product.public.category':
            trash = set(c['id'] for c in filter(lambda c: c['parentId'] == 0 and (u'Varumärken - ' not in c['metaTitle_sv']), remote_categs))
        elif self._name == 'product.category':
            trash = set(c['id'] for c in filter(lambda c: c['parentId'] == 0 and (u'Varumärken - ' in c['metaTitle_sv']), remote_categs))
        done = False
        while not done:
            done = True
            i = 0
            while i < len(remote_categs):
                c = remote_categs[i]
                if c['id'] in trash or c['parentId'] in trash:
                    trash.add(c['id'])
                    del remote_categs[i]
                    done = False
                else:
                    i += 1

        for categ in self:
            if not self.search_count([('id', '=', categ.id), ('parent_id', 'child_of', wgr_top_category.id)]):
                # Not a WGR category
                continue
            if categ.wkg_id and not overwrite:
                continue
            for rcat in remote_categs:
                if rcat['title_%s' % lang] != categ.name:
                    continue
                match = True
                # Different categories can have the same name. Check entire hierarchy.
                parent_id = rcat['parentId']
                cur_categ = categ.parent_id
                while parent_id:
                    parent = filter(lambda c: c['id'] == parent_id, remote_categs)[0]
                    parent_id = parent['parentId']
                    _logger.debug('id: %s, parentId: %s, title_%s: %s, cur_categ: %s' % (
                        parent['id'],
                        parent['parentId'],
                        lang, parent['title_%s' % lang],
                        cur_categ and cur_categ.name))
                    if not cur_categ or cur_categ.name != parent['title_%s' % lang]:
                        match = False
                        break
                    cur_categ = cur_categ.parent_id
                if match and cur_categ != wgr_top_category:
                    # Check that we're at the top of the Odoo category tree as well
                    match = False
                if match:
                    _logger.debug('matched %s (%s) with wkg_id %s' % (
                        categ.name,
                        categ.id,
                        rcat['id']))
                    categ.wkg_id = rcat['id']
                    break

class ProductCategory(models.Model):
    _inherit = 'product.category'
    
    wkg_id = fields.Integer(string='WGR ID', help="The ID of this category in Wikinggruppen.")
    
    _sql_constraints = [('wkg_id_uniq', 'unique (wkg_id)', "The Wikinggruppen category must be unique.")]
    
    @api.multi
    def wkg_update_id(self, overwrite=False):
        """Try to match this category to the corresponding category in Wikinggruppen."""
        connector = self.env['website'].wkg_get_connector()
        lang = (self.env.context.get('lang') or self.env.user.lang).split('_')[0]
        remote_categs = connector.wkg_function('Category.get', {})
        # Filtering is specific to KR. Special Brand categories.
        if self._name == 'product.public.category':
            trash = set(c['id'] for c in filter(lambda c: c['parentId'] == 0 and (u'Varumärken - ' not in c['metaTitle_sv']), remote_categs))
        elif self._name == 'product.category':
            trash = set(c['id'] for c in filter(lambda c: c['parentId'] == 0 and (u'Varumärken - ' in c['metaTitle_sv']), remote_categs))
        _logger.warn(trash)
        done = False
        while not done:
            done = True
            i = 0
            while i < len(remote_categs):
                c = remote_categs[i]
                if c['id'] in trash or c['parentId'] in trash:
                    _logger.warn('%s, %s, %s' % (c['id'], c['parentId'], c['title_sv']))
                    trash.add(c['id'])
                    del remote_categs[i]
                    done = False
                else:
                    i += 1

        for categ in self:
            if categ.wkg_id and not overwrite:
                continue
            for rcat in remote_categs:
                if rcat['title_%s' % lang] != categ.name:
                    continue
                match = True
                # Different categories can have the same name. Check entire hierarchy.
                parent_id = rcat['parentId']
                cur_categ = categ.parent_id
                while parent_id:
                    parent = filter(lambda c: c['id'] == parent_id, remote_categs)[0]
                    parent_id = parent['parentId']
                    _logger.debug('id: %s, parentId: %s, title_%s: %s, cur_categ: %s' % (
                        parent['id'],
                        parent['parentId'],
                        lang, parent['title_%s' % lang],
                        cur_categ and cur_categ.name))
                    if not cur_categ or cur_categ.name != parent['title_%s' % lang]:
                        match = False
                        break
                    cur_categ = cur_categ.parent_id
                if match:
                    _logger.debug('matched %s (%s) with wkg_id %s' % (
                        categ.name,
                        categ.id,
                        rcat['id']))
                    categ.wkg_id = rcat['id']
                    break

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    wkg_product = fields.Boolean('WGR Product', help="This product should be copied to Wikinggruppen.", default=False)
    wkg_productid = fields.Integer('WGR Parent ID', help="productId. The id corresponding to a template. Seems completely useless in all practical matters, but here it is.")
    wkg_parent_code = fields.Char('WGR Parent Code', help="externalParentArticleNumber. This is how WGR actually identifies templates.")
    wkg_description = fields.Text('WGR Description', translate=True)

    
    @api.one
    def wkg_fetch_descriptions(self):
        """Update descriptions for this template from Wikinggruppen."""
        for product in self.product_variant_ids:
            if product.wkg_id:
                product.wkg_fetch_descriptions()
                break

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    wkg_id_number = fields.Char('Organization Number')                  # *sigh* This doesn't appear to actually be used in the orders we get from the webshop.
    wkg_vat = fields.Char('VAT Number')
    wkg_customer = fields.Boolean('WGR Customer', help="This checkbox will be checked if this customer was synced from Wikinggruppen.")
    # ~ wkg_id = fields.Integer('WGR Id', help="The ID of this product in Wikinggruppen.")
    
    # ~ _sql_constraints = [('wkg_id_uniq', 'unique (wkg_id)', "The Wikinggruppen category must be unique.")]
    
    @api.model
    def wkg_check_vat(self, vat):
        """Same check as in core, but returns True/False instead of raise."""
        if self.env.user.company_id.vat_check_vies:
            # force full VIES online check
            check_func = self.vies_vat_check
        else:
            # quick and partial off-line checksum validation
            check_func = self.simple_vat_check
        vat_country, vat_number = self._split_vat(vat)
        return check_func(vat_country, vat_number)

    @api.model
    def wkg_get_address(self, values):
        warnings = []
        country = self.env['res.country'].search([('code', '=', values[u'countryCode'])])
        if not country and values[u'countryCode']:
            warnings.append("Couldn't match countryCode %s for %%s." % values[u'countryCode'])
        state = values[u'state'] and country and self.env['res.country.state'].search([('code', '=', values[u'state']), ('country_id', '=', country.id)])
        if not state and values[u'state']:
            warnings.append("Couldn't match state %s for %%s." % values[u'state'])
        vals = {
            'name': '%s %s' % (values['firstName'], values['lastName']),
            'street': values[u'streetRow1'],
            'street2': (values[u'streetRow2'] or u'') + (values[u'streetRow3'] and ' %s' % values[u'streetRow3'] or u''),
            'zip': values[u'zipCode'],
            'city': values[u'city'],
            'country_id': country and country.id or False,
            'state_id': state and state.id or False,
            'wkg_id_number': values[u'idNumber'],
            'wkg_vat': values[u'VATNumber'],
            'vat': values[u'VATNumber'],
        }
        if vals['vat'] and not self.wkg_check_vat(vals['vat']):
            warnings.append("VATNumber %s is not valid for %%s." % vals['vat'])
            del vals['vat']
        # Remove redundant names from contacts
        if vals['name'] == values['fullName']:
            del vals['name']
        domain = [(key, '=', vals[key]) for key in vals]
        return (vals, domain, warnings)

class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    wkg_id = fields.Integer(string='WGR Id', help="The ID of this product in Wikinggruppen.")
    
    _sql_constraints = [('wkg_id_uniq', 'unique (wkg_id)', "The Wikinggruppen category must be unique.")]
    
    @api.multi
    def wkg_mapping(self, pricelists=None, partner=None):
        """Map this product to the corresponding fields in Wikinggruppen."""
        self.ensure_one()
        #website = self.env.ref('website.default_website')
        website = self.env['website']
        connector = website.wkg_get_connector()
        if not self.public_categ_ids:
            raise Warning(_("%s (%s) must have at least one public category!") % (self.name, self.id))
        if not all(c.wkg_id for c in self.public_categ_ids):
            raise Warning(_("%s (%s) category must have a wkg_id!") % (self.public_categ_ids[0].name, self.public_categ_ids[0].id))
        warehouse = website.wkg_get_warehouse()
        wh_rule = self.env['stock.warehouse.orderpoint'].search([('product_id', '=', self.id), ('warehouse_id', '=', warehouse.id)], limit=1)
        quantities = self.with_context(warehouse=warehouse.id)._compute_quantities_dict(None, None, None)[self.id]
        categories = sorted(list(set([c.wkg_id for c in self.public_categ_ids] + ([self.categ_id.wkg_id] if self.categ_id else []))))
        values = {
            'articleNumber': self.default_code,
            'EANCode': self.barcode or '',
            'weight': int(self.weight),# * 1000, # grammes
            # ~ 'price_SEK': self.lst_price,
            'categoryId': categories,              #templatenivå
            #'price_EUR': '',    # Don't have these yet.
            #'': 'standard_price', # Doesn't seem like we use supplier prices?
            # ~ 'campaignPrice_SEK': self.campaign_price,
            'VATRate': int(self.taxes_id and self.taxes_id[0].amount or 0),
            'isHidden': not (self.active and self.website_published),
            # ~ 'producer': self.categ_id and self.categ_id.name or '',
            'stockPlace': wh_rule and wh_rule.location_id.name or '',
            'stock': int(quantities['qty_available']),
        }

        for lang in website.wkg_get_languages():
            trans_obj = self.env['product.product'].with_context(lang=lang.code).browse(self.id)
            lang = lang.code.split('_')[0]
            values.update({
                'title_%s' % lang: trans_obj.name,                      #templatenivå
                'description_%s' % lang: trans_obj.wkg_description, #templatenivå
                'phrase_%s' % lang: trans_obj.description_sale or '',         #KR-specifik. Ej i API-beskrivningen.
            })
        pricelists = pricelists or website.wkg_get_pricelists()
        partner = partner or self.env['ir.model.data'].get_object('base', 'public_user')
        for field in pricelists:
            values[field] = pricelist.get_product_price(self, 1, partner)
        return values
    
    @api.one
    def wkg_update_id(self, wkg_values=None):
        """Try to match this product to the corresponding product in Wikinggruppen."""
        if not self.default_code:
            raise Warning(_("%s (%s) doesn't have an article number (default_code).") % (product.name, product.id))
        if not wkg_values:
            connector = self.env['website'].wkg_get_connector()
            wkg_values = connector.article_get(article_nr=self.default_code)
        if wkg_values:
            if wkg_values and len(wkg_values) > 1:
                raise Warning(_("Found several matching products for [%s] %s (%s)") % (self.default_code, self.name, self.id))
            wkg_values = wkg_values[0]
            self.wkg_id = wkg_values['id']
            if self.wkg_productid and (self.wkg_productid != wkg_values['productId']):
                raise Warning(_("Mismatch between Odoo and WGR when syncing %s (%s). Products WGR Product ID (%s) doesn't match the productId from WGR (%s).") % (self.name, self.id, self.wkg_productid, wkg_values['productId']))
            self.wkg_productid = wkg_values['productId']
            if self.wkg_parent_code and (self.wkg_parent_code != wkg_values['externalParentArticleNumber']):
                raise Warning(_("Mismatch between Odoo and WGR when syncing %s (%s). Products WGR Parent Code (%s) doesn't match the externalParentArticleNumber from WGR (%s).") % (self.name, self.id, self.wkg_parent_code, wkg_values['externalParentArticleNumber']))
            self.wkg_parent_code = wkg_values['externalParentArticleNumber']
    
    @api.one
    def wkg_push(self):
        connector = self.env['website'].wkg_get_connector()
        wkg_values = connector.article_get(self.wkg_id, self.default_code)
        if wkg_values and len(wkg_values) > 1:
            raise Warning(_("Found several matching products for [%s] %s (%s)") % (self.default_code, self.name, self.id))
        wkg_values = wkg_values and wkg_values[0] or None
        if not self.wkg_id:
            self.wkg_update_id(wkg_values)
        if not self.wkg_id:
            self.wkg_create()
        else:
            self.wkg_write(wkg_values)
    
    @api.one
    def wkg_write(self, wkg_values):
        connector = self.env['website'].wkg_get_connector()
        if not self.public_categ_ids[0].wkg_id:
            raise Warning(_("%s (%s) category must have a wkg_id!") % (self.public_categ_ids[0].name, self.public_categ_ids[0].id))
        if not wkg_values:
            wkg_values = connector.article_get(id=self.wkg_id)
        # For some reason categoryId is a list of strings. The documentation claims it should be int.
        wkg_values[u'categoryId'] = sorted([int(id) for id in wkg_values[u'categoryId']])
        values = self.wkg_mapping()
        for key in values.keys():
            if values[key] == wkg_values[key]:
                del values[key]
                del wkg_values[key]
        # ~ raise Warning('%s\n%s' % (values, wkg_values))
        if values:
            values['id'] = self.wkg_id
            result = connector.wkg_function('Article.set', values)
            _logger.warn(result)
    
    @api.one
    def wkg_create(self):
        connector = self.env['website'].wkg_get_connector()
        if not self.default_code:
            raise Warning(_("%s (%s) is missing Internal Reference (default_code).") % (self.name, self.id))
        if not self.wkg_parent_code:
            if self.wkg_productid:
                raise Warning(_("%s (%s) can not be synced to WGR, because the product template has no externalParentArticleNumber."))
            self.wkg_parent_code = self.default_code
        values = self.wkg_mapping()
        values.update({
            'externalParentArticleNumber': self.wkg_parent_code,
            'options': [],
        })
        languages = self.env['website'].wkg_get_languages()
        for attr in self.attribute_value_ids:
            option = {}
            for lang in languages:
                trans_attr = attr.with_context(lang=lang.code).browse(attr.id)
                option.update({
                    'title_%s' % lang.code.split('_')[0]: trans_attr.attribute_id.name,
                    'value_%s' % lang.code.split('_')[0]: trans_attr.name,
                    # hexcode? Ser inte den i någon API-koppling.
                })
            values['options'].append(option)
        # ~ raise Warning(str(values))
        res = connector.wkg_function('Article.create', values)
        self.wkg_productid = res['productId']
        self.wkg_id = res['id']
        # It's possible that the article number has been altered to keep it unique.
        # I haven't seen this in practice, but the documentation insists it can happen.
        self.default_code = res['articleNumber']
    
    @api.one
    def wkg_fetch_descriptions(self):
        connector = self.env['website'].wkg_get_connector()
        wkg_values = connector.article_get(id=self.wkg_id)[0]
        for lang in self.env['website'].wkg_get_languages():
            trans_obj = self.env['product.product'].with_context(lang=lang.code).browse(self.id)
            lang = lang.code.split('_')[0]
            trans_obj.wkg_description= wkg_values['description_%s' % lang]

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'
    
    wkg_id = fields.Integer(string='WGR Id', help="The ID of this shipping method in Wikinggruppen.")

class SaleOrderWkgStatus(models.Model):
    _name = 'sale.order.wkg.status'
    
    wkg_id = fields.Integer(string='WGR Id', help="The ID of this order status in Wikinggruppen.", required=True)
    name = fields.Char(required=True)
    
    _sql_constraints = [('wkg_id_uniq', 'unique (wkg_id)', "Wikinggruppen saleorder id must be unique.")]
    
    @api.model
    def wkg_get_order_statuses(self):
        website = self.env['website']
        connector = website.wkg_get_connector()
        for status in connector.wkg_function('OrderStatus.get', {}):
            loc_status = self.search([('wkg_id', '=', status['id'])])
            if loc_status and loc_status.name != status['title']:
                loc_status.name = title
            else:
                self.create({'wkg_id': status['id'], 'name': status['title']})
            
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    wkg_id = fields.Integer(string='WGR Id', help="The ID of this order line in Wikinggruppen.")
            
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    wkg_id = fields.Integer(string='WGR Id', help="The ID of this order in Wikinggruppen.")
    wkg_time = fields.Datetime('WGR Time', help="The time when the order was created in Wikinggruppen.")
    wkg_status_id = fields.Many2one(string='WGR Status', comodel_name='sale.order.wkg.status')
    wkg_warnings = fields.Text('Warnings', help="These warnings were generated when importing from Wikinggruppen.")
    wkg_currency_rate = fields.Float('Currency Rate')
    wkg_payment_method = fields.Char('Payment Method')
    wkg_klarna = fields.Boolean('Klarna')
    wkg_klarna_api = fields.Char('API version')
    wkg_klarna_reservation = fields.Char('Reservation Id')
    wkg_klarna_eid = fields.Char('Merchant Id')
    wgr_best_message = fields.Char('Best Message')
    wgr_message = fields.Char('Delivery Message')
    wgr_delivery_date = fields.Char('Delivery Date')
    wgr_door_code = fields.Char('Door Code')
    
    # This works poorly because Odoo insists on writing 0 to all integer/float columns. Thanks a lot, Odoobama.
    #_sql_constraints = [('wkg_id_uniq', 'wkg_id = 0 OR unique (wkg_id)', "Wikinggruppen saleorder id must be unique.")]
    
    @api.model
    def wkg_get_order_customer(self, values):
        # Fields from Customer object that are missing on the order client:
        # ('isFreeShipping', 'isRetail', 'priceListId', 'id')
        warnings = []
        res_partner = self.env['res.partner']
        billing, b_domain, b_warn = res_partner.wkg_get_address(values['billingAddress'])
        shipping, s_domain, s_warn = res_partner.wkg_get_address(values['shippingAddress'])
        billing_ids = [r['id'] for r in res_partner.search_read(b_domain + [('type', '=', 'invoice')], ['id'])]
        shipping_ids = [r['id'] for r in res_partner.search_read(s_domain + [('type', '=', 'delivery')], ['id'])]
        vals = {
            'name': values['billingAddress']['fullName'],
            'email': values[u'email'],
            'phone': values[u'telephone'],
            'mobile': values[u'cellphone'],
            'is_company': values[u'isCompany'],
            'street': shipping[u'street'],
            'street2': shipping[u'street2'],
            'zip': shipping[u'zip'],
            'city': shipping[u'city'],
            'country_id': shipping[u'country_id'],
            'state_id': shipping[u'state_id'],
            'wkg_id_number': shipping[u'wkg_id_number'],
            'vat': shipping[u'vat'],
        }
        domain = [(key, '=', vals[key]) for key in vals] + [('child_ids', 'in', billing_ids), ('child_ids', 'in', shipping_ids), ('parent_id', '=', False)]
        customer = self.env['res.partner'].search(domain, limit=1)
        if not customer:
            for line in s_warn:
                warnings.append(line % 'shippingAddress')
            for line in b_warn:
                warnings.append(line % 'billingAddress')
            vals['wkg_customer'] = True
            customer = res_partner.create(vals)
            for type, vals in (('invoice', billing), ('delivery', shipping)):
                vals.update({
                    'type': type,
                    'parent_id': customer.id,
                })
                res_partner.create(vals)
        return customer, warnings
        
    @api.model
    def wkg_get_new_orders(self, id=None, from_id=None, from_time=None, order_status=None, front_id=None):
        website = self.env['website']
        connector = website.wkg_get_connector()
        params = {}
        if id:
            params = {'id': id}
        elif from_id:
            params = {'fromId': from_id}
        elif from_time:
            params = {'fromTime': from_time[:19]}
        elif order_status:
            params = {'orderStatus': order_status}
        elif front_id:
            params = {'frontId': front_id}
        wkg_orders = connector.wkg_function('Order.get', params)
        orders = self.browse()
        if not wkg_orders:
            return orders
        pricelists = website.wkg_get_pricelists(campaigns=False, per_field=False)
        public_pl = self.env['ir.model.data'].get_object('product', 'list0')
        languages = website.wkg_get_languages()
        taxes = website.wkg_get_taxes()
        wkg_statuses = {}
        wkg_carriers = {}
        for status in self.env['sale.order.wkg.status'].search_read([], ['wkg_id']):
            wkg_statuses[status['wkg_id']] = status['id']
        for carrier in self.env['delivery.carrier'].search_read([('wkg_id', '!=', False)], ['wkg_id']):
            wkg_carriers[carrier['wkg_id']] = carrier['id']
        for wkg_values in wkg_orders:
            order = self.search([('wkg_id', '=', wkg_values['id'])])
            if order:
                # Order already exists. Update values?
                order.wkg_warnings = '\n'.join([order.wkg_warnings or '', '', fields.Datetime.now(), "Got new values for order %s. No changes have been made." % wkg_values['id'], str(wkg_values)])
                orders |= order
                continue
            customer, warnings = self.wkg_get_order_customer(wkg_values['client'])
            # Update customer language
            for language in languages:
                if language.code.split('_')[0] == wkg_values['languageCode']:
                    if customer.lang != language.code:
                        customer.lang = language.code
                    break
            pricelist = pricelists.get(wkg_values['currencyCode'])
            if not pricelist:
                warnings.append("Couldn't find a pricelist for currencyCode %s." % wkg_values['currencyCode'])
                pricelist = public_pl
            # Fix the order status. Current customer use statuses 'Nya', 'Nekad Order' and 'Arkiverade' (not in actual use, but exists).
            if wkg_values['orderStatus']:
                # Ids as strings again...
                wkg_values['orderStatus'] = wkg_statuses.get(int(wkg_values['orderStatus']), False)
            carrier = False
            if wkg_values['shippingMethodId']:
                carrier = wkg_carriers.get(int(wkg_values['shippingMethodId']), False)
                if not carrier:
                    warnings.append("Couldn't match shippingMethodId %s to a carrier." % wkg_values['shippingMethodId'])
            lines = []
            for row in wkg_values['items']:
                product = self.env['product.product'].search([('default_code', '=', row['articleNumber'])])
                if len(product) > 1:
                    warnings.append("Found multiple matches for articleNumber %s. Picked one at random." % row['articleNumber'])
                    product = product[0]
                if not product:
                    warnings.append("No match found for articleNumber %s." % row['articleNumber'])
                tax = taxes.get(row['VATRate'])
                if not tax:
                    warnings.append("Couldn't find a tax for VATRate %s." % row['VATRate'])
                if not product:
                    warnings.append("Row could not be created. See previous errors. Values: %s." % row)
                    continue
                lines.append((0, 0, {
                    'wkg_id': row['rowId'],
                    'product_id': product and product.id,
                    'name': row['title'],
                    'tax_id': [(6, 0, [tax.id])] if tax else [],
                    'product_uom_qty': row['quantity'],
                    'price_unit': float(row['price']),
                }))
            if warnings:
                warnings = [fields.Datetime.now()] + warnings
            values = {
                'partner_id': customer.id,
                'wkg_id': wkg_values['id'],
                'wkg_time': wkg_values['orderTime'],
                'carrier_id': carrier,
                'pricelist_id': pricelist.id,
                'order_line': lines,
                'wkg_status_id': wkg_statuses.get(wkg_values['orderStatus'], False),
                'wkg_payment_method': wkg_values['payMethod'],
                'note': wkg_values['message'],
                'wkg_warnings': '\n'.join(warnings),
                'wgr_best_message': wkg_values.get('bestMessage'),
                'wgr_message': wkg_values.get('message'),
                'wgr_delivery_date': wkg_values.get('deliveryDate'),
                'wgr_door_code': wkg_values.get('doorCode'),
            }
            klarna = wkg_values.get('klarna')
            if klarna:
                values['wkg_klarna'] = True
                values['wkg_klarna_api'] = klarna['api']
                values['wkg_klarna_reservation'] = klarna['reservation']
                values['wkg_klarna_eid'] = klarna['eid']
            order = self.env['sale.order'].create(values)
            # Recompute everything to get correct values
            for field in ('partner_id', 'partner_shipping_id', 'partner_invoice_id'):
                order._onchange_eval(field, "1", {})
            # ~ order.onchange_partner_id()                                 # partner_id
            # ~ order.onchange_partner_shipping_id()                        # partner_shipping_id, partner_id
            for line in order.order_line:
                l = filter(lambda l: l[2]['wkg_id'] == line.wkg_id, lines)[0][2]
                # Perform onchanges
                for field in ('product_id', 'product_uom', 'product_uom_qty'):
                    line._onchange_eval(field, "1", {})
                # Reset to price, tax and name from WGR.
                line.write({
                    'price_unit': l['price_unit'],
                    'tax_id': l['tax_id'],
                    'name': l['name'],
                })
                # Perform onchanges for tax and price
                for field in ('price_unit', 'tax_id'):
                    line._onchange_eval(field, "1", {})
            for field in ('fiscal_position_id', 'order_line'):
                order._onchange_eval(field, "1", {})
            # ~ order._compute_tax_id()                                     # fiscal_position_id
            orders |= order
        return orders

class WikinggruppenWizard(models.TransientModel):
    _name = 'wkg.wizard'
    _description = 'Wikinggruppen Wizard'
    
    wkg_id = fields.Integer('WGR Id', help="Id of the order you want to sync.")
    from_time = fields.Datetime('From Time', help="Sync all orders from this date (and time).")
    
    def sync_orders(self, id=None, from_time=None):
        if id:
            orders = self.env['sale.order'].wkg_get_new_orders(id=id)
        elif from_time:
            orders = self.env['sale.order'].wkg_get_new_orders(from_time=from_time)
        action = self.env['ir.actions.act_window'].for_xml_id('sale', 'act_res_partner_2_sale_order')
        action.update({
            'domain': [('id', 'in', [o.id for o in orders])],
            'context': {},
        })
        return action
    
    def action_sync_by_id(self):
        if not self.wkg_id:
            raise Warning("You must supply an order id.")
        return self.sync_orders(id=self.wkg_id)
    
    def action_sync_by_from_time(self):
        if not self.from_time:
            raise Warning("You must supply a time.")
        return self.sync_orders(from_time=self.from_time)
        

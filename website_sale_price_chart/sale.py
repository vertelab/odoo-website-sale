# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2018 Vertel AB (<http://vertel.se>).
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

import logging
_logger = logging.getLogger(__name__)


class pricelist_chart_type(models.Model):
    """
        Key -> pricelist
        Gives:
            Pricelist for price
            Pricelist for recommended price
            Use account.tax if tax should be added

    """
    _name = "pricelist_chart.type"
    _description = "Pricelist Chart Type"

    name = fields.Char()
    pricelist = fields.Many2one(comodel_name='product.pricelist',help='This pricelist is used to choose price-listing', required=True)
    price_tax  = fields.Many2one(comodel_name='account.tax',help="Use this tax for price calculatopon, none if tax is not included.")
    price_product_tax  = fields.Boolean(string="Use Product Tax",comodel_name='account.tax',help='Use product tax for price instread of tax for price in this record')
    rec_pricelist = fields.Many2one(comodel_name='product.pricelist')
    rec_price_tax  = fields.Many2one(string="Tax for rec price",comodel_name='account.tax',help='Use this tax for rec price, none if tax is not included. (unless Use product Tax is checked)')
    rec_price_product_tax  = fields.Boolean(string="Use Product Tax (Rec)",comodel_name='account.tax',help='Use product tax for rec price instread of tax for rec price in this record')
    

    @api.multi
    def calc(self, product_id):
        for pl_type in self:
            self.env['product.pricelist_chart'].search([('product_id','=',product_id), ('pricelist_chart_id','=',pl_type.id)]).unlink()
            pl = self.env['product.pricelist_chart'].sudo().create({'product_id': product_id,'pricelist_chart_id': pl_type.id})
            pl.price = pl_type.pricelist.price_get(product_id, 1)[pl_type.pricelist.id]
            _logger.warn('price %s' % pl.price)
            if pl_type.price_product_tax:
                taxes = self.env['product.product'].browse(product_id).taxes_id
                if len(taxes) > 0:
                    for tax in taxes:
                        pl.price += sum(map(lambda x: x.get('amount', 0.0),tax.compute_all(pl.price, 1, None, self.env.user.partner_id)['taxes']))
                    pl.price_tax = True
            else:
                if pl_type.price_tax:
                    pl.price += sum(map(lambda x: x.get('amount', 0.0), pl_type.sudo().price_tax.compute_all(pl.price, 1, None, self.env.user.partner_id)['taxes']))
                    pl.price_tax = True
            if pl_type.rec_pricelist:
                pl.rec_price = pl_type.rec_pricelist.price_get(product_id, 1)[pl_type.rec_pricelist.id]
                if pl_type.rec_price_product_tax:
                    for tax in self.env['product.product'].browse(product_id).taxes_id:
                        pl.rec_price += sum(map(lambda x: x.get('amount', 0.0),tax.compute_all(pl.rec_price, 1, None, self.env.user.partner_id)['taxes']))
                    pl.rec_price_tax = True
                elif pl_type.rec_price_tax:
                    pl.rec_price += sum(map(lambda x: x.get('amount', 0.0), pl_type.sudo().rec_price_tax.compute_all(pl.rec_price, 1, None, self.env.user.partner_id)['taxes']))
                    pl.rec_price_tax = True
            else:
                pl.rec_price = None
        return pl

    @api.multi
    def price_get(self, product):
        price = product.pricelist_chart_ids.filtered(lambda p: p.pricelist_chart_id in self).mapped('price')
        if len(price)>0:
            return price[0]
        else:
            return 0

class product_product(models.Model):
    _inherit = 'product.product'

    pricelist_chart_ids = fields.One2many(comodel_name='product.pricelist_chart',inverse_name='product_id')



    @api.multi
    def calc_pricelist_chart(self):
        for product in self:
            self.env['pricelist_chart.type'].search([]).calc(product.id)





    @api.model
    def calc_pricelist_chart_all(self):
        for product in self.env['product.product'].search([('sale_ok','=',True)]):
            self.env['pricelist_chart.type'].search([]).calc(product.id)




    @api.multi
    def get_pricelist_chart_line(self, pricelist):
        """ returns pricelist line-object  """
        if isinstance(pricelist,int):
            pricelist = self.env['product.pricelist'].browse(pricelist)
        pl_ids = self.env['product.pricelist_chart'].browse()
        pl_type = self.env['pricelist_chart.type'].sudo().search([('pricelist','=',pricelist.id)])
        # start = time.clock()
        # if time.clock() - start > 1:
             
        if not pl_type:
            _logger.warn('could not find sandra')
            pl_type = self.env['pricelist_chart.type'].sudo().create({'name': pricelist.name,'pricelist': pricelist.id})
        # ~ return pl_ids
        #TODO: Code here should be tested
        for product in self:
            if product.sale_ok:
                pl = product.pricelist_chart_ids.filtered(lambda t: t.pricelist_chart_id == pl_type)
                if not pl:
                    pl = pl_type.calc(product.id)
                if len(pl) > 1:
                    pl = pl[0]
                pl_ids |= pl
        return pl_ids
        
    @api.multi
    def get_pricelist_chart_line_type(self, pl_type):
        """ returns pricelist line-object  """
        for product in self:
            if product.sale_ok:
                pl = product.pricelist_chart_ids.filtered(
                    lambda t: t.pricelist_chart_id == pl_type)
                if not pl:
                    pl = pl_type.calc(product.id)
                if len(pl) > 1:
                    pl = pl[0]
                pl_ids |= pl
        return pl_ids




class product_pricelist_chart(models.Model):
    _name = 'product.pricelist_chart'

    product_id = fields.Many2one(comodel_name='product.product')
    pricelist_chart_id = fields.Many2one(comodel_name='pricelist_chart.type')
    price      = fields.Float()
    price_tax  = fields.Boolean()



    def _price_txt_format(self,price,currency):
        lang = self.env['res.lang'].format([self._context.get('lang') or 'en_US'],'%.2f', price, grouping=True, monetary=True)
        text = u'{pre}<span class="oe_currency_value">{0}</span>{post}'.format(
            lang,
            pre=u'{symbol}\N{NO-BREAK SPACE}' if currency.position == 'before' else '',
            post=u'\N{NO-BREAK SPACE}{symbol}' if not currency.position == 'before' else '',
        )
        res = text.format(
            symbol=currency.symbol,
        )
        return res

    @api.one
    def _price_txt(self):

        self.price_txt_short = self._price_txt_format(self.price, self.pricelist_chart_id.pricelist.currency_id)
        self.price_txt       = '%s %s' % (self.price_txt_short + _('your price') if self.price_tax else _('your price excl. tax')  )

        self.rec_price_txt_short = self._price_txt_format(self.rec_price,self.pricelist_chart_id.rec_pricelist.currency_id)
        self.rec_price_txt       = '%s %s' % (self.rec_price_txt_short + _('ca price incl. tax') if self.rec_price_tax else _('ca price excl. tax')  )
        self.rec_price_txt_short = '(%s)' % self.rec_price_txt_short

    price_txt  = fields.Char(compute='_price_txt')
    price_txt_short  = fields.Char(compute='_price_txt')
    rec_price  = fields.Float()
    rec_price_tax = fields.Boolean()
    rec_price_txt  = fields.Char(compute='_price_txt')
    rec_price_txt_short  = fields.Char(compute='_price_txt')


    # ~ @api.model
    # ~ def get_pricelist_chart_html(self,product_id,pricelist_id):
        # ~ """ returns pricelist html  """

        # ~ pl_ids = self.env['product.pricelist_chart'].browse()
        # ~ for product in self:
            # ~ pl_type = self.env['pricelist_chart.type'].search([('pricelist','=',pricelist.id)])
            # ~ if not pl_type:
                # ~ pl_type = self.env['pricelist_chart.type'].sudo().create({'name': pricelist.name,'pricelist': pricelist.id})
            # ~ pl = product.pricelist_chart_ids.filtered(lambda t: t.pricelist_chart_id == pl_type)
            # ~ if not pl:
                # ~ pl = pl_type.calc(product.id)
            # ~ pl_ids |= pl
        # ~ return pl_ids

    @api.multi
    def get_html_price_long(self):
        def price_format(price, dp=None):
            if not dp:
                dp = self.env['res.lang'].search_read([('code', '=', self.env.lang)], ['decimal_point'])
                dp = dp and dp[0]['decimal_point'] or '.'
            return ('%.2f' %price).replace('.', dp)
        def price_txt_format(self,price,currency):
            lang = self.env['res.lang'].format([self._context.get('lang') or 'en_US'], lang,'.2f', price, grouping=True, monetary=True)

            text = u'{pre}<span class="oe_currency_value">{0}</span>{post}'.format(
                lang,
                pre=u'{symbol}\N{NO-BREAK SPACE}' if currency.position == 'before' else '',
                post=u'\N{NO-BREAK SPACE}{symbol}' if not currency.position == 'before' else '',
            )

            res = text.format(
                symbol=currency.symbol,
            )

            return res


        # ~ if isinstance(pricelist,int):
            # ~ pricelist = self.env['product.pricelist'].browse(pricelist)
        # ~ chart_line = self.env['product.template'].browse(product_id).get_pricelist_chart_line(pricelist)
        price = '<!-- pre rec price -->'
        if self.pricelist_chart_id.rec_pricelist:
            if self.env.user.has_group('webshop_dermanord.group_dn_sk'):
                tax=_('(price incl. tax)') if self.price_tax else _('(price excl. tax)')
            if not self.env.user.has_group('webshop_dermanord.group_dn_sk'):
                tax=_('(ca price incl. tax)') if self.price_tax else _('(ca price excl. tax)')

            price = """
                <div style="white-space: nowrap"><!-- rec price -->
                    <span style="white-space: nowrap;" >{name}</span>
                    <span style="white-space: nowrap;" >{price}</span>
                    <span style="display: inline;">{tax}</span>
                </div>
            """.format(name=self.pricelist_chart_id.rec_pricelist.currency_id.name,
                       price=price_format(self.rec_price),
                       tax= tax
                       )

        if self.pricelist_chart_id.pricelist and self.pricelist_chart_id.pricelist.for_reseller:
            price += """
                <div style="white-space: nowrap"><!-- price -->
                    <span style="white-space: nowrap;" >{name}</span>
                    <span style="white-space: nowrap;" class="your_price" data-price="{price_float}"><b>{price}</b></span>
                    <span style="display: inline;">{tax}</span>
                </div>
            """.format(name=self.pricelist_chart_id.pricelist.currency_id.name,
                       price=price_format(self.price),
                       price_float=self.price,
                       tax=_('(your price incl. tax)') if self.price_tax else _('(your price excl. tax)')
                       )

        if self.pricelist_chart_id.pricelist and not self.pricelist_chart_id.pricelist.for_reseller:
            if self.env.user.has_group('webshop_dermanord.group_dn_sk'):
                tax=_('(price incl. tax)') if self.price_tax else _('(price excl. tax)')
            if not self.user.env.has_group('webshop_dermanord.group_dn_sk'):
                tax=_('(ca price incl. tax)') if self.price_tax else _('(ca price excl. tax)')

            price += """
                <div style="white-space: nowrap"><!-- public price -->
                    <span style="white-space: nowrap;" >{name}</span>
                    <span style="white-space: nowrap;" ><b>{price}</b></span>
                    <span style="display: inline;">{tax}</span>
                </div>
            """.format(name=self.pricelist_chart_id.pricelist.currency_id.name,
                       price=price_format(self.price),
                       tax=tax
                       )
        return """
            <div>
                {price}
            </div>
        """.format(price=price)

    @api.multi
    def get_html_price_short(self):
        def price_format(price, dp=None):
            if not dp:
                dp = self.env['res.lang'].search_read([('code', '=', self.env.lang)], ['decimal_point'])
                dp = dp and dp[0]['decimal_point'] or '.'
            return ('%.2f' %price).replace('.', dp)
        def price_txt_format(self,price,currency):
            return u'{pre}<span class="oe_currency_value">{0}</span>{post}'.format(
                self.env['res.lang'].format([self._context.get('lang') or 'en_US'],'.2f', price,grouping=True, monetary=True),
                pre=u'{symbol}\N{NO-BREAK SPACE}' if currency.position == 'before' else '',
                post=u'\N{NO-BREAK SPACE}{symbol}' if not currency.position == 'before' else '',
            ).format(
                symbol=currency.symbol,
            )
        price = ''
        if self.pricelist_chart_id.pricelist:
            price += """
                <h5><!-- price -->
                    <span style="white-space: nowrap;"  class="your_price" data-price="{price_float}"><b>{price}</b></span>
                    <span style="white-space: nowrap;" >{name}</span>
                </h5>
            """.format(name=self.pricelist_chart_id.pricelist.currency_id.name,
                       price=price_format(self.price),
                       price_float=self.price
                       )
        if self.pricelist_chart_id.rec_pricelist:
            price += """
                <h5><!-- rec price -->
                    (<span style="white-space: nowrap;" >{price}</span>
                    <span style="white-space: nowrap;" >{name}</span>)
                </h5>
            """.format(name=self.pricelist_chart_id.rec_pricelist.currency_id.name,
                       price=price_format(self.rec_price),
                       )

        return price


class product_template(models.Model):
    _inherit = 'product.template'

    @api.multi
    def get_pricelist_chart_line(self, pricelist):
        """ returns cheapest pricelist line  """
        pl_ids = self.env['product.pricelist_chart'].browse()
        for product in self:
            if product.product_variant_ids:
                pl_ids |= product.product_variant_ids.get_pricelist_chart_line(pricelist).sorted(key=lambda p: p.price, reverse=False)[0]
        return pl_ids

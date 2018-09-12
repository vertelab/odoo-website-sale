# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2015 Vertel AB (<http://vertel.se>).
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
    pricelist = fields.Many2one(comodel_name='product.pricelist',help='This pricelist is used to choose price-listing')
    price_tax  = fields.Many2one(comodel_name='account.tax',help="Use this tax for price calculatopon, none if tax is not included.")
    rec_pricelist = fields.Many2one(comodel_name='product.pricelist')
    rec_price_tax  = fields.Many2one(string="Tax for rec price",comodel_name='account.tax',help='Use this tax for rec price, none if tax is not included')

    @api.multi
    def calc(self,product):
        for pl_type in self:
            pl = self.env['product.pricelist_chart'].search([('product_id','=',product.id),('pricelist_chart_id','=',pl_type.id)])
            if not pl:
                pl = self.env['product.pricelist_chart'].create({'product_id': product.id,'pricelist_chart_id': pl_type.id})
            pl.price = pl_type.pricelist.price_get(product.id, 1)[pl_type.pricelist.id]
            _logger.warn('price %s' % pl.price)
            if pl_type.price_tax:
                pl.price + sum(map(lambda x: x.get('amount', 0.0), pl_type.price_tax.compute_all(pl.price, 1, None, self.env.user.partner_id)['taxes']))
                pl.price_tax = True
            if pl_type.rec_pricelist:
                pl.rec_price = pl_type.rec_pricelist.price_get(product.id, 1)[pl_type.rec_pricelist.id]
                if pl_type.rec_price_tax:
                    pl.rec_price + sum(map(lambda x: x.get('amount', 0.0), pl_type.rec_price_tax.compute_all(pl.rec_price, 1, None, self.env.user.partner_id)['taxes']))
                    pl.rec_price_tax = True
            else:
                pl.rec_price = None
        return pl

class product_product(models.Model):
    _inherit = 'product.product'
    
    pricelist_chart_ids = fields.One2many(comodel_name='product.pricelist_chart',inverse_name='product_id')
    
    @api.multi
    def calc_pricelist_chart(self):
        for product in self:
            self.env['pricelist_chart.type'].search([]).calc(product)
 
    @api.model
    def calc_pricelist_chart_all(self):
        for product in self.env['product.product'].search([('sale_ok','=',True)]):
            self.env['pricelist_chart.type'].search([]).calc(product)
            
            
    @api.multi
    def get_pricelist_chart_line(self,pricelist):
        """ returns pricelist line  """
        pl_ids = self.env['product.pricelist_chart'].browse()
        for product in self:
            pl_type = self.env['pricelist_chart.type'].search([('pricelist','=',pricelist.id)])
            if not pl_type:
                pl_type = self.env['pricelist_chart.type'].create({'name': pricelist.name,'pricelist': pricelist.id})
            pl = product.pricelist_chart_ids.filtered(lambda t: t.pricelist_chart_id == pl_type)
            if not pl:
                pl = pl_type.calc(product)
            pl_ids |= pl
        return pl_ids
            
class product_pricelist_chart(models.Model):
    _name = 'product.pricelist_chart'

    product_id = fields.Many2one(comodel_name='product.product')
    pricelist_chart_id = fields.Many2one(comodel_name='pricelist_chart.type') 
    price      = fields.Float()
    price_tax  = fields.Boolean()
    
    def _price_txt_format(self,price,currency):
        return u'{pre}<span class="oe_currency_value">{0}</span>{post}'.format(
                self.env['res.lang'].format([self._context.get('lang') or 'en_US'],'%.2f', price,grouping=True, monetary=True),
                pre=u'{symbol}\N{NO-BREAK SPACE}' if currency.position == 'before' else '', 
                post=u'\N{NO-BREAK SPACE}{symbol}' if not currency.position == 'before' else '',
            ).format(
                symbol=currency.symbol,
            )
    
    @api.one
    def _price_txt(self):

        self.price_txt_short = self._price_txt_format(self.price,self.pricelist_chart_id.pricelist.currency_id)
        self.price_txt       = '%s %s' % (self.price_txt_short + _('your incl. tax') if self.price_tax else _('your excl. tax')  )

        self.rec_price_txt_short = self._price_txt_format(self.rec_price,self.pricelist_chart_id.rec_pricelist.currency_id)
        self.rec_price_txt       = '%s %s' % (self.rec_price_txt_short + _('your incl. tax') if self.rec_price_tax else _('your excl. tax')  )
        self.rec_price_txt_short = '(%s)' % self.rec_price_txt_short
        
    price_txt  = fields.Char(compute='_price_txt')
    price_txt_short  = fields.Char(compute='_price_txt')
    rec_price  = fields.Float()
    rec_price_tax = fields.Boolean()
    rec_price_txt  = fields.Char(compute='_price_txt')
    rec_price_txt_chort  = fields.Char(compute='_price_txt')

class product_template(models.Model):
    _inherit = 'product.template'

    @api.model
    def get_pricelist_chart_line(self,pricelist):
        """ returns cheapest pricelist line  """
        return self.variant_ids.get_pricelist_chart_line(pricelist).sorted(key=price, reverse=True)[0]
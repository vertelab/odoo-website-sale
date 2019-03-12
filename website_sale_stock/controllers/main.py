# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp.addons.website_sale.controllers.main import website_sale
from openerp.http import request
from openerp import http

import logging

_logger = logging.getLogger(__name__)

class website_sale(website_sale):
    def _get_combination_info(self, product_template_id, product_id, combination, add_qty, pricelist, **kw):
        """deprecated, use product method"""
        combination = request.env['product.template.attribute.value'].browse(combination)
        return request.env['product.template'].browse(int(product_template_id))._get_combination_info(combination, product_id, add_qty, pricelist)

    @http.route(['/shop/get_stock_values'], type='json', auth="public", methods=['POST'], website=True)
    def get_stock_values(self, product_id, **kw):

        # ~ _logger.warn(product_id)
        
        product = request.env['product.product'].browse(int(product_id))
        
        # ~ _logger.warn(product)
        
        return {'qty_available'         :product.qty_available, 
                'inventory_availability':product.inventory_availability,
                'available_threshold'   :product.available_threshold,
                'custom_message'        :product.custom_message,
                'product_type'          :product.type,
                'virtual_available'     :product.virtual_available,
                'product_template'      :product.product_tmpl_id.id,
                'uom_name'              :product.uom_id.name,
                'cart_qty'              :product.cart_qty,
                'product_type'          :product.type,
                }

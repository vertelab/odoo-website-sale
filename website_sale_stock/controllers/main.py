# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp.addons.website_sale.controllers.main import website_sale
from openerp.http import request
from openerp import http

class website_sale(website_sale):
    @http.route(['/shop/get_stock_values'], type='json', auth="public", methods=['POST'], website=True)
    def get_stock_values(self, product_id, **kw):

        product = request.env['product.product'].browse(int(product_id))
        
        return {'qty_available'         :product.qty_available,                 # qty available for sale
                'inventory_availability':product.inventory_availability,        # 'always', 'threshold', 'never'
                'available_threshold'   :product.available_threshold,           # int if 'inventory_availability' is 'threshold' 
                'custom_message'        :product.custom_message,                # used for setting a custom availability message
                'product_type'          :product.type,                          # 'product', 'consumable', etc.
                'virtual_available'     :product.virtual_available,             # ???
                'product_template'      :product.product_tmpl_id.id,
                'uom_name'              :product.uom_id.name,
                'cart_qty'              :product.cart_qty,                      # qty in current customer's cart
                # ~ 'product_type'          :product.type,                          # duplicate? removed without testing...
                'is_edu_purchase'       :False,
                }

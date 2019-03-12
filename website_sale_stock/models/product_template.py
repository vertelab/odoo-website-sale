# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    @api.model
    def default_inventory_availability(self):
        return self.env['ir.config_parameter'].get_param('website_sale_stock.inventory_availability', 'never')

    @api.model
    def default_available_threshold(self):
        return float(self.env['ir.config_parameter'].get_param('website_sale_stock.available_threshold', '5.0'))

    inventory_availability = fields.Selection([
        ('never', 'Sell regardless of inventory'),
        ('always', 'Show inventory on website and prevent sales if not enough stock'),
        ('threshold', 'Show inventory below a threshold and prevent sales if not enough stock'),
        ('custom', 'Show product-specific notifications'),
    ], string='Inventory Availability', help='Adds an inventory availability status on the web product page.', default=default_inventory_availability)
    available_threshold = fields.Float(string='Availability Threshold', default=default_available_threshold)
    custom_message = fields.Text(string='Custom Message', default='')

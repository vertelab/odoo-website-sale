# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'sale.config.settings'

    inventory_availability = fields.Selection([
        ('never', 'Sell regardless of inventory'),
        ('always', 'Show inventory on website and prevent sales if not enough stock'),
        ('threshold', 'Show inventory below a threshold and prevent sales if not enough stock'),
        ('custom', 'Show product-specific notifications'),
    ], string='Inventory Availability', default='never')
    available_threshold = fields.Float(string='Availability Threshold')

    @api.one
    def set_inventory_availability(self):
        self.env['ir.config_parameter'].set_param('website_sale_stock.inventory_availability', self.inventory_availability)
        self.env['ir.config_parameter'].set_param('website_sale_stock.available_threshold', str((self.available_threshold if self.inventory_availability == 'threshold' else 0) or 0))

    @api.model
    def get_default_inventory_availability(self, fields):
        inventory_availability=self.env['ir.config_parameter'].get_param('website_sale_stock.inventory_availability', 'never')
        available_threshold=float(self.env['ir.config_parameter'].get_param('website_sale_stock.available_threshold', '5.0'))
        return {'inventory_availability': inventory_availability, 'available_threshold': available_threshold}

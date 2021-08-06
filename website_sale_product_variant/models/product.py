# -*- coding: utf-8 -*-

import logging
from odoo import _, api, fields, models
from odoo.osv import expression
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def get_default_variant(self):
        self.ensure_one()
        if not self.product_variant_ids:
            _logger.warn('%s has not variant' %self)
        else:
            return self.product_variant_ids.filtered(lambda v: v.default_variant == True) or (self.product_variant_ids[0] if self and len(self.product_variant_ids) > 0 else None)
        return None

class ProductProduct(models.Model):
    _inherit = 'product.product'

    default_variant = fields.Boolean(string='Default Variant')
    
    @api.constrains('default_variant')
    def _constrain_default_variant(self):
        for variant in self:
            defaults = variant.product_tmpl_id.product_variant_ids.filtered('default_variant')
            if len(defaults) > 1:
                raise ValidationError(_("A template can not have more than one default variant."))

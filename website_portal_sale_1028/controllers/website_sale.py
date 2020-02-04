# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2017- Vertel AB (<http://vertel.se>).
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
from openerp import http
from openerp.http import request
import werkzeug
# from openerp.addons.website_portal_sale_1028.website_sale import main website_portal_1028

import math

import logging
_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit='sale.order.line'

    @api.multi
    def sale_home_confirm_copy(self):
        """Check if this order line should be copied. Override to handle fees and whatnot."""
        return True

class SaleOrder(models.Model):
    _inherit='sale.order'

    @api.multi
    def my_order_state_frontend(self):
        """Get a customer friendly order state."""
        state = None
        if self.state == 'cancel':
            state = _('Cancelled')
        elif self.state in ('shipping_except', 'invoice_except'):
            state = _('Exception')
        elif self.state in ('sent'):
            state = _('Received')
        elif self.state in ('draft'):
            state = _('Cart')
        else:
            state = _('Ready for picking')
            for invoice in self.invoice_ids:
                if invoice.state == 'open' and invoice.residual == invoice.amount_total:
                    state = _('Shipped and invoiced')
                elif invoice.state == 'open' and invoice.residual != invoice.amount_total:
                    state = _('Partially paid')
                elif invoice.state == 'paid':
                    state = _('Paid')
        return state
        
    @api.multi
    def my_order_state_per_invoice_frontend(self):
        """Get a customer friendly order state per invoice."""
        state = []
        if self.state == 'cancel':
            state.append(_('Cancelled'))
        elif self.state in ('shipping_except', 'invoice_except'):
            state.append(_('Exception'))
        elif self.state in ('sent'):
            state.append(_('Received'))
        elif self.state in ('draft'):
            state.append(_('Cart'))
        else:
            state.append(_('Ready for picking'))
            invoices = self.invoice_ids.filtered(lambda i: i.state not in ('draft', 'proforma', 'proforma2'))
            if invoices:
                state = []
                if len(invoices) == 1:
                    if invoices[0].state == 'open' and invoices[0].residual == invoices[0].amount_total:
                        state.append(_('Shipped and invoiced'))
                    elif invoices[0].state == 'open' and invoices[0].residual != invoices[0].amount_total:
                        state.append(_('Partially paid'))
                    elif invoices[0].state == 'paid':
                        state.append(_('Paid'))
                # only print invoice numbers if there are several
                else:
                    # check if all invoices for order are fully paid.
                    if all([invoice.state == "paid" for invoice in invoices]):
                        state.append(_('Paid'))
                    else:
                        for invoice in invoices:
                            if invoice.state == 'open' and invoice.residual == invoice.amount_total:
                                state.append(_('Invoice') + ' ' + invoice.number + ': ' + _('Shipped and invoiced'))
                            elif invoice.state == 'open' and invoice.residual != invoice.amount_total:
                                state.append(_('Invoice') + ' ' + invoice.number + ': ' + _('Partially paid'))
                            elif invoice.state == 'paid':
                                state.append(_('Invoice') + ' ' + invoice.number + ': ' + _('Paid'))
        return state

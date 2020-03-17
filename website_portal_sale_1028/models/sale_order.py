# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import api, exceptions, models, _
import math

class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.multi
    def order_state_frontend(self):
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
    def order_state_per_invoice_frontend(self):
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

    @api.cr_uid_id_context
    def get_access_action(self, cr, uid, id, context):
        """ Instead of the classic form view, redirect to the online quote for
        portal users that have access to a confirmed order. """
        # TDE note: read access on sale order to portal users granted to followed sale orders
        env = api.Environment(cr, uid, context)
        record = env[self._name].browse(id)
        if record.state == 'cancel' or (record.state == 'draft' and not env.context.get('mark_so_as_sent')):
            return super(SaleOrder, self).get_access_action(cr, uid, id, context)
        if env.user.share or env.context.get('force_website'):
            try:
                self.check_access_rule(cr, uid, id, 'read', context)
            except exceptions.AccessError:
                pass
            else:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/my/orders/%s' % id,
                    'target': 'self',
                    'res_id': id,
                }
        return super(SaleOrder, self).get_access_action(cr, uid, id, context)

    @api.multi
    def _notification_recipients(self, message, groups):
        groups = super(SaleOrder, self)._notification_recipients(message, groups)

        self.ensure_one()
        if self.state not in ('draft', 'cancel'):
            for group_name, group_method, group_data in groups:
                group_data['has_button_access'] = True

        return groups

    def _force_lines_to_invoice_policy_order(self):
        for line in self.order_line:
            if self.state in ['sale', 'done']:
                line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    def check_document_access(self, report, ids):
        partner = request.env.user.commercial_partner_id
        model = None
        if report == 'sale.report_saleorder':
            model = 'sale.order'
        elif report == 'account.report_invoice':
            model = 'account.invoice'
        elif report == 'stock_delivery_slip.stock_delivery_slip':
            model = 'stock.picking'
        if model:
            try:
                records = request.env[model].browse(ids)
                # Check partner_id.
                if all([r.partner_id.commercial_partner_id == partner for r in records.sudo()]):
                    return True
                # Check ordinary access controls
                records.check_access_rights('read')
                records.check_access_rule('read')
                return True
            except:
                # This check failed. Let it go to super to perform other checks.
                pass
        return super(website_sale_home, self).check_document_access(report, ids)


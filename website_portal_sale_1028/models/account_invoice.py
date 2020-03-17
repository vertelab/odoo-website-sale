# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import api, exceptions, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _notification_recipients(self, message, groups):
        groups = super(AccountInvoice, self)._notification_recipients(message, groups)

        for group_name, group_method, group_data in groups:
            group_data['has_button_access'] = True

        return groups

    @api.cr_uid_id_context
    def get_access_action(self, cr, uid, id, context):
        """ Instead of the classic form view, redirect to the online invoice for portal users. """
        env = api.Environment(cr, uid, context)
        if env.user.share:
            try:
                self.check_access_rule(cr, uid, [id], 'read', context)
            except exceptions.AccessError:
                pass
            else:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/my/invoices',  # No controller /my/invoices/<int>, only a report pdf
                    'target': 'self',
                    'res_id': id,
                }
        return super(AccountInvoice, self).get_access_action(cr, uid, id, context)

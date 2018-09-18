# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2018- Vertel AB (<http://vertel.se>).
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
from openerp.exceptions import except_orm, Warning, RedirectWarning, AccessError
from openerp import http
from openerp.http import request
import werkzeug
import base64
import sys
import traceback

import logging
_logger = logging.getLogger(__name__)

class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def last_issue(self):
        issues = self.env['project.issue'].search([('partner_id', '=', self.commercial_partner_id.id), ('project_id', '=', self.env.ref('website_sale_home_issue.project_support').id), ('stage_id', 'not in', [self.env.ref('project.project_tt_deployment').id, self.env.ref('project.project_tt_cancel').id])], order='date desc')
        return issues[0] if len(issues) > 0 else None


class website_sale_home(http.Controller):

    @http.route(['/home/issue/send_message'], type='json', auth="user", website=True)
    def send_issue_message(self, issue_id=0, partner_id=None, msg_body='', **kw):
        if msg_body:
            partner = request.env.user.partner_id.commercial_partner_id
            if issue_id != 0:
                issue = request.env['project.issue'].sudo().browse(issue_id)
                if request.env.user.partner_id not in issue.message_follower_ids:
                    issue.sudo().message_subscribe_users([request.env.user.id])
                body = msg_body
                issue.message_post(subject=_('%s wrote:' %request.env.user.partner_id.name), body=body, author_id=request.env.user.partner_id.id, type='comment')
            # first time send message, take the partner name and datetime as name, body as description
            else:
                issue = request.env['project.issue'].sudo().create({
                    'name': '%s - %s' %(partner.name, fields.Datetime.now()),
                    'partner_id': partner.id,
                    'description': msg_body,
                    'stage_id': request.env.ref('project.project_tt_analysis').id,
                    'project_id': request.env.ref('website_sale_home_issue.project_support').id,
                })
                issue.sudo().message_subscribe_users([request.env.user.id])
                return 'new'
        return 'old'

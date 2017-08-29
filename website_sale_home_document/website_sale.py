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
from openerp.addons.website_sale_home.website_sale import website_sale_home


from cStringIO import StringIO


import logging
_logger = logging.getLogger(__name__)



class website(models.Model):
    _inherit="website"

    @api.model
    def sale_home_document_get(self,user,domain):
        _logger.warn('partner %s' % user.partner_id.name)
        if not domain:
            domain = [('partner_id','child_of',user.partner_id.parent_id.id if user.partner_id.parent_id else user.partner_id.id)]
            domain = [('parent_id','=','public')]
            #~ if user.partner_id.parent_id:
                #~ domain.append(('partner_id','child_of',user.partner_id.parent_id.id))
        _logger.warn('%s %s' % (domain,self.env['ir.attachment'].sudo().search(domain)))
        return self.env['ir.attachment'].sudo().search(domain)

    @api.model
    def sale_home_directory_get(self,user):
        return self.env['document.directory'].sudo().search([('name','=','public')])


class website_sale_home(website_sale_home):


    @http.route(['/home/<model("res.users"):home_user>/document/<model("ir.attachment"):document>','/home/<model("res.users"):home_user>/document_report/<model("ir.actions.report.xml"):report>','/home/<model("res.users"):home_user>/documents'], type='http', auth="user", website=True)
    def home_page_document(self, home_user=None, document=None,report=None, tab='document', **post):
        self.validate_user(home_user)

        if report:
            #~ pdf = request.env['report'].get_pdf(request.env['res.partner'].search([]),report.get_external_id()[report.id], data=None)
            pdf = request.env['report'].get_pdf(request.env['res.partner'].search([]),report.report_name, data=None)
            return request.make_response(pdf, headers=[('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))])

        if document:
            _logger.warn('%s %s %s'%(document.datas_fname.replace(' ', '_'),document.mimetype,document.write_date))
            return http.send_file(StringIO(document.datas.decode('base64')), filename=document.datas_fname.replace(' ', '_'), mimetype=document.mimetype or '', mtime=document.write_date, as_attachment=True)
        return request.website.render('website_sale_home_claim.page_documents', {
            'home_user': home_user,
            'documents': request.env['ir.attachment'].search([('partner_id', '=', home_user.partner_id.id)]),
            'tab': tab,
        })


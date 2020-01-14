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


class knowledge_config_settings(models.TransientModel):
    _inherit = 'knowledge.config.settings'

    document_directory = fields.Char(string='Document Directory Domain', help='Specify the document directory domain')

    @api.one
    def set_params(self):
        self.env['ir.config_parameter'].set_param('website_sale_home_document.document_directory', self.document_directory)

    @api.model
    def get_params(self, fields):
        return {'document_directory': self.env['ir.config_parameter'].get_param('website_sale_home_document.document_directory')}

class website(models.Model):
    _inherit="website"

    @api.model
    def sale_home_document_get(self, user, domain):
        if not domain:
            domain = "[('parent_id.name', '=', 'public')]"
        return self.env['ir.attachment'].sudo().search(eval(domain))

    @api.model
    def sale_home_document_type_get(self, doc):
        suffix = ''
        mime_to_type = {'application/pdf': 'pdf',
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
                        'application/vnd.ms-excel': 'xls',
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
                        'application/vnd.ms-office': 'xlm',
                        }

        suffix = mime_to_type.get(doc.mimetype)
        if not suffix: 
            suffix = mime_to_type.get(doc.file_type)
        if not suffix:
            if 'PDF' in doc.name:
                suffix = 'pdf'
            elif 'Excel' in doc.name:
                suffix = 'xls'
        _logger.warn(suffix)
        return (('/%s' % doc.id) + '.' + suffix) if suffix else ''

    @api.model
    def sale_home_directory_get(self, user):
        return self.env['document.directory'].sudo().search([('name', '=', 'public')])


class document_directory_content(models.Model):
    _inherit = 'document.directory.content'

    domain = fields.Char()


class website_sale_home(website_sale_home):

    # ~ @http.route(['/home/<model("res.users"):home_user>/document/<model("ir.attachment"):document>','/home/<model("res.users"):home_user>/document_report/<model("document.directory.content"):report>','/home/<model("res.users"):home_user>/documents'], type='http', auth="user", website=True)
    @http.route(['/home/<model("res.users"):home_user>/document/<int:document>',
                 '/home/<model("res.users"):home_user>/document/<int:document>/<docname>',
                 '/home/<model("res.users"):home_user>/document_report/<model("document.directory.content"):report>',
                 '/home/<model("res.users"):home_user>/documents'
                 ], type='http', auth="user", website=True)
    def home_page_document(self, home_user=None, document=None,report=None, docname=None, tab='document', **post):
        self.validate_user(home_user)

        if report:
            #~ raise Warning(request.env[report.report_id.model].search(eval(report.domain or '[]')).mapped('id'))
            #~ pdf = request.env['report'].get_pdf(request.env['res.partner'].search([]),report.get_external_id()[report.id], data=None)
            pdf = report.sudo().report_id.render_report(request.env[report.report_id.model].search(eval(report.domain or '[]')).mapped('id'),report.report_id.report_name, data={})[0]
            #return http.send_file(StringIO(pdf), filename='min file.pdf', mimetype='application/pdf', as_attachment=True)
            return request.make_response(pdf, headers=[('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))])

        if document:
            document = request.env['ir.attachment'].search([('id','=',document)])
            if not document:
                _logger.warn('cannot read document')
            else:
                document = request.env['ir.attachment'].sudo().search([('id','=',document.id)]) #TODO better security-check  check:225 ir_attachment.py  check:71 document.py
                _logger.warn('Try to send %s' % document)
                fname = document.datas_fname.replace(' ', '_') if document.datas_fname else 'file'
                mime = mimetype=document.mimetype or ''
                write_date=document.write_date
                data = document.datas.decode('base64')
                # ~ _logger.warn('%s %s %s'%(document.datas_fname.replace(' ', '_'),document.mimetype,document.write_date))
                _logger.warn('%s %s %s %s'%(fname,mime,write_date,len(data)))
                return http.send_file(StringIO(data), filename=fname, mimetype=mime, mtime=write_date, as_attachment=True)
                # ~ return http.send_file(StringIO(data), filename=fname, mimetype=mime, mtime=write_date)
        return request.website.render('website_sale_home_document.page_documents', {
            'home_user': home_user,
            'documents': request.env['ir.attachment'].search([('partner_id', '=', home_user.partner_id.id)]),
            'tab': tab,
        })

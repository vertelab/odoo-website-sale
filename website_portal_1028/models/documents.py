# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution, third party addon
#    Copyright (C) 2020- Vertel AB (<http://vertel.se>).
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
from openerp.osv import osv

import logging
_logger = logging.getLogger(__name__)


class DocumentDirectory(models.Model):
    _inherit = 'document.directory'

    portal_publish = fields.Boolean(string='Publish In Portal', help="Publish all content in this catalog to portal users. Will still match groups on the catalog if set.")

    @api.multi
    def write(self, values):
        if 'portal_publish' in values:
            # Update portal_publish on children
            domain = [('id', 'child_of', d.id) for d in self]
            domain = ['|' for i in range(len(domain) - 1)] + domain
            domain.append(('id', 'not in', self._ids))
            # Need to loop because there's a bug in the name unique check when we write to more than one record
            for directory in self.search(domain):
                super(DocumentDirectory, directory).write({'portal_publish': values['portal_publish']})
        return super(DocumentDirectory, self).write(values)

class document_directory(osv.osv):
    _inherit = 'document.directory'

    def name_get(self, cr, uid, ids, context=None):
        # This solves an issue when clicking the Documents button on the directory form
        if type(ids) == int:
            ids = [ids]
        return super(document_directory, self).name_get(cr, uid, ids, context=context)

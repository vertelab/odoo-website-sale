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

import logging
_logger = logging.getLogger(__name__)


class DocumentDirectory(models.Model):
    _inherit = 'document.directory'

    publish_hard = fields.Boolean(string='Publish All Content', help="Publish all content in this catalog. Will still match groups on the catalog if set.")

class Attachment(models.Model):
    _inherit = 'ir.attachment'

    def check(self, cr, uid, ids, mode, context=None, values=None):
        """Overwrite check to verify access on directory to validate specifications of doc/access_permissions.rst"""
        _logger.warn('\n\ncheck: %s\n' % ids)
        if not isinstance(ids, list):
            ids = [ids]
        if ids:
            # use SQL to avoid recursive loop on read
            cr.execute('SELECT DISTINCT parent_id from ir_attachment WHERE id in %s AND parent_id is not NULL AND parent_id.publish_hard', (tuple(ids),))
            parent_ids = [parent_id for (parent_id,) in cr.fetchall()]
            if parent_ids:
                self.pool.get('ir.model.access').check(cr, uid, 'document.directory', mode)
                self.pool.get('document.directory').check_access_rule(cr, uid, parent_ids, mode, context=context)
        super(Attachment, self).check(cr, uid, ids, mode, context=context, values=values)
        
        

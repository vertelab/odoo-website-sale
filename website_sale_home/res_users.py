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

import logging
_logger = logging.getLogger(__name__)


#~ class website(models.Model):
    #~ _inherit = 'website'

    #~ share_twitter = fields.Boolean(string='Twitter')
    #~ share_facebook = fields.Boolean(string='Facebook')
    #~ share_googleplus = fields.Boolean(string='GooglePlus')
    #~ #share_youtube = fields.Boolean(string='YouTube')
    #~ #share_linkedin = fields.Boolean()


#~ class website_config_settings(models.TransientModel):
    #~ _inherit = 'website.config.settings'

    #~ share_twitter = fields.Boolean(related='website_id.share_twitter', string='Twitter')
    #~ share_facebook = fields.Boolean(related='website_id.share_facebook', string='Facebook')
    #~ share_googleplus = fields.Boolean(related='website_id.share_googleplus', string='GooglePlus')

    
class website_sale_home(http.Controller):

    @http.route(['/home','/home/<model("res.users"):user>', ], type='http', auth="user", website=True)
    def home_page(self,user=None ,**post):
        if request.uid == ref('base.public_user').id:
            return request.website.render('website.403')
        if not user:
            return werkzeug.utils.redirect("/home/%s" % request.uid)
        
        _logger.warning("This is form postnr %s" % (form))
        return request.render('website_sale_home.home_page', {'user': user if user else request.env['res.users'].browse(request.uid) })


 

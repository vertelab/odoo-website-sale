# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2018 Vertel (<http://vertel.se>).
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


import logging
_logger = logging.getLogger(__name__)

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning

import requests
from requests.auth import HTTPBasicAuth
import json

class WikinggruppenAPI84(object):
    WKG_CLASSES = ['Article', 'Category', 'Customer', 'Front', 'NewsletterRecipient', 'Order', 'OrderStatus', 'PriceList', 'ProductImage', 'ShippingMethod', 'Stock']
    WKG_FUNCTIONS = {
        'Article': ['get', 'create', 'update'],
        'Category': ['get', 'create', 'update'],
        'Customer': ['get', 'create', 'update'],
        'Front': ['get'],
        'NewsletterRecipient': ['get', 'create', 'update', 'delete'],
        'Order': ['get', 'create', 'update', 'cancel', 'restore'],
        'OrderStatus': ['get', 'create', 'update'],
        'PriceList': ['get', 'create', 'update', 'delete'],
        'ProductImage': ['get', 'create', 'delete'],
        'ShippingMethod': ['get'],
        'Stock': ['get', 'update'],
    }
    
    def __init__(self, env):
        self.env = env
    
    def wiking_send_data(self, data):
        username = self.env['ir.config_parameter'].get_param('wikinggruppen.api_key')
        password = self.env['ir.config_parameter'].get_param('wikinggruppen.passwd')
        url = self.env['ir.config_parameter'].get_param('wikinggruppen.url')
        
        headers = {'content-type': 'application/json'}
        
        response = requests.post(
            url,
            json=data,
            auth=HTTPBasicAuth(username, password))
            
        return response.json()
        
response = requests.post('http://localhost:8069//web/webclient/csslist', json={}, verify=False)
            

/web/webclient/csslist mods


data = json.dumps({
    "jsonrpc": "2.0",
    "method": "OrderStatus.get",
})

auth = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')

req = urllib2.Request(url, data, {'Content-Type': 'application/json'})
req.add_header("Authorization", "Basic %s" % auth)









base64string = base64.encodestring('%s:%s' % ('user2', '54321')).replace('\n', '')
req = urllib2.Request('http://localhost/protected')
req.add_header("Authorization", "Basic %s" % base64string)
response = urllib2.urlopen(req)


/web/webclient/csslist mods

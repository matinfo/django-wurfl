from wurfl.conf import settings
from wurfl.models import Update, StandardDevice

from xml import sax
from django.utils.simplejson.encoder import JSONEncoder
from time import time

from django.db import IntegrityError


class _Handler(sax.ContentHandler):
    def __init__(self, device_class=None, update_class=None, merge=False):
        # Parsing version flag
        self.parse_version = False
        # JSON encoder
        self.e = JSONEncoder()
        # Device class
        self.device_class = device_class
        # Update class
        self.update_class = update_class
        # are we merging?
        self.merge = merge
        
    def startElement(self, name, attrs):
        if name == 'wurfl':
            self.start_time = time()
            self.stats = {'nb_devices':0, 'url':settings.URL, 'errors':0}
        elif name == 'ver':
            self.stats['version'] = ''
            self.parse_version = True
        elif name == 'device':
            self.device = {}
            self.device['id'] = attrs.get('id', '')
            self.device['user_agent'] = attrs.get('user_agent', '')
            self.device['fall_back'] = attrs.get('fall_back', '')
            self.device['actual_device_root'] = attrs.get('actual_device_root', False) and True
            # Prepare the capabilities
            self.capabilities = {}
        elif name == 'group':
            self.current_group = attrs.get('id','')
            self.capabilities[self.current_group] = {}
        elif name == 'capability':
            value = attrs.get('value', '')
            if value == 'true' or value == 'false':
                value = (value == 'true')
            elif value.isdigit():
                value = int(value)
                
            self.capabilities[self.current_group][attrs.get('name','')] = value
        
    def endElement(self, name):
        if name == 'device':
            # Process the capabilities
            self.device['json_capabilities'] = self.e.encode(self.capabilities)
            
            # Save the device model
            if self.device_class:
                try:
                    self.device_class.objects.create(**self.device)
                except IntegrityError:
                    if self.merge:
                        device = self.device_class.objects.get(id=self.device['id'])
                        device.merge_json_capabilities(self.device['json_capabilities'])
                        device.save()
                    else:
                        raise
            
            # Update the stats
            self.stats['nb_devices'] += 1
        elif name == 'wurfl':
            # End of the update
            self.stats['time_for_update'] = time() - self.start_time
            
            if self.update_class:
                self.update_class.objects.create(**self.stats)
        elif name == 'ver':
            self.parse_version = False
            
        
    def characters(self, ch):
        if self.parse_version:
            self.stats['version'] += ch
        
def parse_wurfl(content, device_class=StandardDevice, update_class=Update, merge=False):
    parser = sax.make_parser()
    handler = _Handler(device_class, update_class, merge)
    parser.setContentHandler(handler)
    parser.parse(content)
    


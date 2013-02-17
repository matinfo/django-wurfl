from django.core.management.base import CommandError
from django.core.management.base import BaseCommand

from wurfl.models import Device
from wurfl.exceptions import NoMatch

class Command(BaseCommand):
    args = '<user_agents.txt>'
    help = 'Test mobile device type <smartphone|featuredphone> from list of user agent'
    
    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("This command takes exactly one argument")

        try:
            data = []
            with open(args[0],"r") as f:
                [data.append(l) for l in f]

            for user_agent in data:

                device = self.get_device_from_user_agent(user_agent.strip())
                if device:
                    print "%s|%s|%s" % (self.get_device_type(device), user_agent.strip(), self.get_device_name(device))
                else:
                    print "%s|%s" % ('notfund', user_agent.strip())

        except Exception, e:
            if options.get('traceback', False):
                import traceback
                traceback.print_exc()
            else:
                raise CommandError(e)

    def get_device_from_user_agent(self, ua):

        try:
            device = Device.get_from_user_agent(ua)
        except NoMatch:
            device = None
        
        return device

    def get_device_type(self, device):

        if device.get_capability('is_tablet'):
                return 'tablet'
        elif device.get_capability('can_assign_phone_number') and device.get_capability('device_claims_web_support'):
                return 'smartphone'
        elif device.get_capability('can_assign_phone_number'):
                return 'featuredphone'
        return 'notmatch'

    def get_device_name(self, device):

        marketing_name = device.get_capability('marketing_name'),
        model_extra_info = device.get_capability('model_extra_info')

        if marketing_name and model_extra_info:
            extra = '%s %s' % (marketing_name, model_extra_info)
        elif marketing_name:
            extra = '%s' % marketing_name
        elif model_extra_info:
            extra = '%s' % model_extra_info
        else:
            extra = ''

        return '%s %s %s' % (
            device.get_capability('brand_name'), 
            device.get_capability('model_name'), 
            extra)
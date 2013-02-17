import tempfile
from django.contrib import admin
from django.conf.urls.defaults import patterns, url
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

import wurfl
from wurfl import update
from wurfl.models import Update, Device, Patch
from wurfl.forms import WurflImportForm, WurflSearchForm

import operator

class UpdateAdmin(admin.ModelAdmin):
    list_display = ('update_type', 'update_date', 'nb_devices', 'nb_merges', 'time_for_update_pretty', 'no_errors',)
    list_filter = ('update_date',)
    ordering = ('-update_date',)
    
    def update_hybrid_view(self, request):

        if not self.has_add_permission(request):
            raise PermissionDenied

        updates = update.hybrid()

        if any(map(operator.attrgetter('errors'), updates)):
            message_bit = _('There was some errors when computing the hybrid table, please check the error report')
        else:
            message_bit = _('Hybrid table build successfully')

        self.message_user(request, "%s" % message_bit)
        return HttpResponseRedirect(reverse('admin:wurfl_update_changelist'))
 
    def update_wurfl_view(self, request):

        if not self.has_add_permission(request):
            raise PermissionDenied
        
        context = RequestContext(request)
        
        opts = self.model._meta
        app_label = opts.app_label

        context.update({
            'opts': opts,
            'root_path': getattr(self.admin_site, 'root_path', None),
            'has_add_permission': self.has_add_permission(request),
            'current_app': self.admin_site.name,
            'app_label': app_label,
            'original': 'Import',
            'model_admin': self
        })

        if request.method == 'GET':
            form = WurflImportForm()
        else:
            form = WurflImportForm(data=request.POST, files=request.FILES)
            if form.is_valid():
                temp_file = tempfile.NamedTemporaryFile(mode='w+b', delete=True)
                for chunk in request.FILES['xml_file'].chunks():
                    temp_file.write(chunk)
                temp_file.seek(0)
                stats = update.wurfl(temp_file.name)
                temp_file.close()

                self.message_user(request, "%s %s: %s" %
                    (stats.get_update_type_display(), _(' updated successfully'), mark_safe(stats.summary)))
                return HttpResponseRedirect(reverse('admin:wurfl_update_changelist'))

        context['media'] = self.media + form.media
        context['adminform'] = form

        return render_to_response('admin/wurfl/import.html', context)

    def search_wurfl_view(self, request):

        if not self.has_add_permission(request):
            raise PermissionDenied
        
        context = RequestContext(request)
        
        opts = self.model._meta
        app_label = opts.app_label

        context.update({
            'opts': opts,
            'root_path': getattr(self.admin_site, 'root_path', None),
            'has_add_permission': self.has_add_permission(request),
            'current_app': self.admin_site.name,
            'app_label': app_label,
            'original': 'Search',
            'model_admin': self
        })

        if request.method == 'GET':
            form = WurflSearchForm()
        else:
            form = WurflSearchForm(data=request.POST)
            if form.is_valid():
                user_agent = form.cleaned_data['user_agent']
                if user_agent:
                    if form.cleaned_data['test']:
                        devices = Device.get_from_user_agent(user_agent)
                    else:
                        ds = Device.objects.filter(user_agent=user_agent)
                        ds = ds.order_by('-actual_device_root')
                        devices = []
                        for d in ds:
                            d._build_full_capabilities()
                            devices.append(d)
                    if not hasattr(devices, '__iter__'):
                        devices = [devices]

                    context['form'] = WurflSearchForm(data=request.POST)
                    context['devices'] = devices
                    context['user_agent'] = user_agent
        context['media'] = self.media + form.media
        context['adminform'] = form
        
        return render_to_response('admin/wurfl/search.html', context, context_instance=RequestContext(request))
        
    #def change_view(self, request, object_id, extra_context=None):
    #    up = Update.objects.get(pk=object_id)
    #    return render_to_response('admin/wurfl/update/change_form.html',
    #        {'object':up,
    #         'opts':self.model._meta},context_instance=RequestContext(request))
    
    def get_urls(self):
        urlpatterns = patterns('',
            url(r'^build/$', self.admin_site.admin_view(self.update_hybrid_view), name="admin_wurfl_build_hybrid"),
            url(r'^import/$', self.admin_site.admin_view(self.update_wurfl_view), name="admin_wurfl_update_wurfl"),
            url(r'^search/$', self.admin_site.admin_view(self.search_wurfl_view), name="admin_wurfl_search_wurfl"),
        )
        return urlpatterns + super(UpdateAdmin, self).get_urls()
    
class PatchAdmin(admin.ModelAdmin):
    ist_display = ('name', 'priority', 'updated', 'created', 'active')
    list_filter = ('active', 'priority',)
    search_fields = ('name',)


# Register WURFL Admins
admin.site.register(Update, UpdateAdmin)
admin.site.register(Patch, PatchAdmin)


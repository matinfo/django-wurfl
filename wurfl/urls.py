from django.conf.urls.defaults import url, patterns


urlpatterns = patterns('wurfl.views',
	url(r'^test/$', 'test', name='wurfl-test'),
)
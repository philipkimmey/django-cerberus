from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

from cerberus.views import permissions_view
from cerberus.views import permissions_edit

urlpatterns = patterns('',
    # Example:
    # (r'^cerberus/', include('cerberus.foo.urls')),
    (r'^permissions/view/(?P<clsname>[a-z]+)(?:/(?P<obj_pk>[-\w]*))?/$', permissions_view),
    
    (r'^permissions/edit/(?P<clsname>[a-z]+)(?:/(?P<obj_pk>[-\w]*))?/$', permissions_edit),

    (r'^admin/', include(admin.site.urls)),
)

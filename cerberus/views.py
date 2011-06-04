from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template import RequestContext
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

import cerberus

from cerberus.models import UserObjectPermission
from cerberus.models import GroupObjectPermission
from cerberus.models import UserClassPermission
from cerberus.models import GroupClassPermission

def permissions_edit(request, clsname=None, obj_pk=None):
    pass

def permissions_view(request, clsname=None, obj_pk=None):
    if clsname is None and obj_pk is None:
        raise Exception("Must specify and class and optionally an object")
    if clsname is not None:
        cls = None
        for cerb_cls in cerberus.get_classes():
            if cerb_cls.__name__.lower() == clsname:
                cls = cerb_cls
        content_type = cerberus.get_class_content_type(cls)
    if not issubclass(cls, models.Model):
        raise Exception("Class was invalid or did not have cerb perms")
    obj = None
    if obj_pk is not None:
        obj = cls.objects.get(pk=obj_pk)
    # handle class perms
    class_perms = cerberus.get_class_perms(cls)
    users = User.objects.all()
    groups = Group.objects.all()
    ucp = UserClassPermission.objects.filter(content_type=content_type)
    gcp = GroupClassPermission.objects.filter(content_type=content_type)
    group_class_perms = {}
    for g in groups:
        group_class_perms[g] = set()
        for perm in gcp.filter(group=g).values('codename'):
            group_class_perms[g].add(perm['codename'])
        g.class_perms = group_class_perms[g]
    for u in users:
        u.class_perms = {}
        for perm in ucp.filter(user=u).values('codename'):
            u.class_perms[perm['codename']] = 'User permission on ' + cls.__name__
        perms_set = set(u.class_perms)
        for g in u.groups.all():
            new_perms = group_class_perms[g] - perms_set
            for nperm in new_perms:
                u.class_perms[nperm] = 'Permission received from group: ' + unicode(g)
        if u.is_superuser:
            for cls_perm in class_perms:
                u.class_perms[cls_perm] = 'User receives permission as superuser.'
    if obj is None:
        return render_to_response('cerberus/class_perms.html',
                {'class_perms': class_perms, 'users': users, 'groups': groups, 'clsname': cls.__name__},
                context_instance=RequestContext(request))
    object_perms = cerberus.get_object_perms(cls)
    uop = UserObjectPermission.objects.filter(content_type=content_type, object_pk=obj_pk)
    gop = GroupObjectPermission.objects.filter(content_type=content_type, object_pk=obj_pk)
    group_object_perms = {}
    for g in groups:
        group_object_perms[g] = set()
        for perm in gop.filter(group=g).values('codename'):
            group_object_perms[g].add(perm['codename'])
        g.object_perms = group_object_perms[g]
    for u in users:
        u.object_perms = {}
        for perm in ucp.filter(user=u).values('codename'):
            u.object_perms[perm['codename']] = 'User permission on %s "%s"' % (cls.__name__, unicode(obj))
        perms_set = set(u.object_perms)
        for g in u.groups.all():
            new_perms = group_object_perms[g] - perms_set
            for nperm in new_perms:
                u.object_perms[nperm] = 'Permission received from group: %s' % unicode(g)
        if u.is_superuser:
            for obj_perm in object_perms:
                u.object_perms[obj_perm] = 'User receives permission as superuser.'
    return render_to_response('cerberus/object_perms.html',
            {'class_perms': class_perms, 'object_perms': object_perms, 'users': users, 'groups': groups, 'clsname': cls.__name__, 'object': obj},
            context_instance=RequestContext(request))

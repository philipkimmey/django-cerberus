from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

import cerberus

from cerberus.models import UserObjectPermission
from cerberus.models import GroupObjectPermission
from cerberus.models import UserClassPermission
from cerberus.models import GroupClassPermission

def __get_cls_obj_and_content_type(clsname, obj_pk):
    (cls, obj) = (None, None)
    for cerb_cls in cerberus.get_classes():
        if cerb_cls.__name__.lower() == clsname:
            cls = cerb_cls
    if cls is None:
        raise Exception("Invalid class name.")
    content_type = cerberus.get_class_content_type(cls)
    if obj_pk is not None:
        obj = cls.objects.get(pk=obj_pk)
    return (cls, obj, content_type)

def __get_users_and_groups(cls, obj=None):
    users = User.objects.all()
    groups = Group.objects.all()
    content_type = cerberus.get_class_content_type(cls)
    class_perms = cerberus.get_class_perms(cls)
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
        u.class_perms_user_only = set()
        for perm in ucp.filter(user=u).values('codename'):
            u.class_perms[perm['codename']] = 'User permission on %s' % cls.__name__
            u.class_perms_user_only.add(perm['codename'])
        perms_set = set(u.class_perms)
        for g in u.groups.all():
            for nperm in (group_class_perms[g] - perms_set):
                u.class_perms[nperm] = 'Permission received from group: %s' % unicode(g)
        if u.is_superuser:
            for cls_perm in class_perms:
                u.class_perms[cls_perm] = 'User receives permission as superuser.'
    if obj is None:
        return (users, groups)
    uop = UserObjectPermission.objects.filter(content_type=content_type, object_pk=obj.pk)
    gop = GroupObjectPermission.objects.filter(content_type=content_type, object_pk=obj.pk)
    object_perms = cerberus.get_object_perms(cls)
    group_object_perms = {}
    for g in groups:
        # handle regular GroupObjectPermissions
        group_object_perms[g] = set()
        for perm in gop.filter(group=g).values('codename'):
            group_object_perms[g].add(perm['codename'])
        g.object_perms = group_object_perms[g]
        g.object_perms_group_only = group_object_perms[g]
        # handle group object perms inherited from class perms
        # TODO
    for u in users:
        # handle regular UserObjectPermissions
        u.object_perms_user_only = set()
        u.object_perms = {}
        for perm in uop.filter(user=u).values('codename'):
            u.object_perms_user_only.add(perm['codename'])
            u.object_perms[perm['codename']] = 'User permission on %s %s' % (cls.__name__, unicode(obj))
        for g in u.groups.all():
            for nperm in (group_object_perms[g] - perms_set):
                u.object_perms[nperm] = 'Permission received from group: %s' % unicode(g)
        if u.is_superuser:
            for obj_perm in object_perms:
                u.object_perms[obj_perm] = 'User receives permission as superuser.'
        # handle user object perms inherited from class perms
        # TODO
    return (users, groups)

def __get_add_rm_perms(request, group_or_user, pk, add_or_rm):
    """

    """
    perms = request.POST.getlist(group_or_user + '_perms_' + unicode(pk))
    perms_original = request.POST.getlist(group_or_user + '_perms_original_' + unicode(pk))
    perms = set(perms)
    perms_original = set(perms_original)
    if add_or_rm == 'add':
        return perms - perms_original
    else:
        return perms_original - perms

def __handle_form_submit(request, cls, obj, content_type):
    obj_or_cls = None
    if obj is None:
        obj_or_cls = cls
    else:
        obj_or_cls = obj
    for group in Group.objects.all():
        for perm in __get_add_rm_perms(request, 'group', group.pk, 'add'):
            group.set_perm(perm, obj_or_cls)
        for perm in __get_add_rm_perms(request, 'group', group.pk, 'rm'):
            group.remove_perm(perm, obj_or_cls)
    for user in User.objects.all():
        for perm in __get_add_rm_perms(request, 'user', user.pk, 'add'):
            user.set_perm(perm, obj_or_cls)
        for perm in __get_add_rm_perms(request, 'user', user.pk, 'rm'):
            user.remove_perm(perm, obj_or_cls)
    if obj is None:
        return HttpResponseRedirect(cls.get_class_permissions_url())
    else:
        return HttpResponseRedirect(obj.get_object_permissions_url())

def permissions_edit(request, clsname, obj_pk=None):
    (cls, obj, content_type) = __get_cls_obj_and_content_type(clsname, obj_pk)
    if request.method == 'POST':
        return __handle_form_submit(request, cls, obj, content_type)
    (users, groups) = __get_users_and_groups(cls, obj)
    class_perms = cerberus.get_class_perms(cls)
    object_perms = cerberus.get_object_perms(cls)
    if obj is None:
        return render_to_response('cerberus/class_perms_edit.html',
                {'class_perms': class_perms,
                    'users': users, 'groups': groups,
                    'clsname': cls.__name__, 'class': cls},
                context_instance=RequestContext(request))
    return render_to_response('cerberus/object_perms_edit.html',
            {'class_perms': class_perms, 'object_perms': object_perms,
                'users': users, 'groups': groups, 
                'clsname': cls.__name__, 'object': obj},
            context_instance=RequestContext(request))

def permissions_view(request, clsname, obj_pk=None):
    (cls, obj, content_type) = __get_cls_obj_and_content_type(clsname, obj_pk)
    (users, groups) = __get_users_and_groups(cls, obj)
    class_perms = cerberus.get_class_perms(cls)
    object_perms = cerberus.get_object_perms(cls)
    if obj is None:
        return render_to_response('cerberus/class_perms_view.html',
                {'class_perms': class_perms,
                    'users': users, 'groups': groups,
                    'clsname': cls.__name__, 'class': cls},
                context_instance=RequestContext(request))
    return render_to_response('cerberus/object_perms_view.html',
            {'class_perms': class_perms, 'object_perms': object_perms,
                'users': users, 'groups': groups, 
                'clsname': cls.__name__, 'object': obj},
            context_instance=RequestContext(request))

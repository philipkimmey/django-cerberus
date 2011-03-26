import django.db.models.options as options
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

options.DEFAULT_NAMES += ('cerberus', 'cerberus_implies', 'cerberus_mutex')

import models

def get_permission_types(obj):
    perms = ()
    if hasattr(obj.__class__._meta, 'cerberus'):
        perms += obj.__class__._meta.cerberus
    subclses = obj.__class__.__bases__
    while subclses:
        next_subclses = ()
        for subcls in subclses:
            next_subclses += subcls.__bases__
            if hasattr(subcls, '_meta') and hasattr(subcls._meta, 'cerberus'):
                perms += subcls._meta.cerberus
        subclses = next_subclses
    perm_dicts = []
    for p in perms:
        perm_dicts.append({'name': p[0], 'display': p[1], 'description': p[2]})
    return perm_dicts

def _set_perm(self, permission, obj):
    content_type = ContentType.objects.get_for_model(obj.__class__)
    if isinstance(self, User):
        pmo = models.UserObjectPermission(user=self, codename=permission, content_type=content_type, object_pk=obj.pk)
    else:
        pmo = models.GroupObjectPermission(group=self, codename=permission, content_type=content_type, object_pk=obj.pk)
    pmo.save()

def _remove_perm(self, permission, obj):
    content_type = ContentType.objects.get_for_model(obj.__class__)
    if isinstance(self, User):
        pmo = models.UserObjectPermission.objects.filter(user=self).filter(codename=permission).filter(content_type=content_type).get(object_pk=obj.pk)
    else:
        pmo = models.GroupObjectPermission.objects.filter(group=self).filter(codename=permission).filter(content_type=content_type).get(object_pk=obj.pk)
    pmo.delete()

def get_perms(self, obj):
    content_type = ContentType.objects.get_for_model(obj.__class__)
    response = set()
    perm_objs = models.UserObjectPermission.objects.filter(content_type=content_type).filter(object_pk=obj.pk).filter(user=self)
    for po in perm_objs:
        response.add(po.codename)
    return set(response)

setattr(User, 'set_perm', _set_perm)
setattr(Group, 'set_perm', _set_perm)
setattr(User, 'remove_perm', _remove_perm)
setattr(Group, 'remove_perm', _remove_perm)
setattr(User, 'get_perms', get_perms)
setattr(Group, 'get_perms', get_perms)

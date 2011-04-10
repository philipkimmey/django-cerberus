from django.db.models.signals import class_prepared
import django.db.models.options as options
from django.db.models import Model
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

options.DEFAULT_NAMES += ('cerberus', 'cerberus_implies', 'cerberus_mutex')

import models

"""
When __init__ is first compiled, we generate a dictionary of Models to 
permissions. This should allow us to detect illegally formatted permission
tuples, as well as allow for fast lookups later.
"""

class CerberusPermission(object):
    def __init__(self, cls, codename, text, description, abstract=False, *args, **kwargs):
        self.cls = cls
        self.codename = codename
        self.text = text
        self.description = description
        self.abstract = abstract
    def clone_non_abstract(self, cls, *args, **kwargs):
        return CerberusPermission(cls=cls, codename=self.codename, text=self.text,
            description=self.description)

class CerberusModelPermission(object):
    """
    This class is used only in __init__ for bookkeeping.
    self.object_perms & self.class_perms consist of dicts of permission
    codenames followed by a permission.
    """
    def __init__(self, *args, **kwargs):
        self.cls = kwargs.pop('cls')
        self.object_perms = {}
        self.class_perms = {}
    def get_object_perm_residence(self, perm):
        pass
    def get_class_perm_residence(self, perm):
        pass


perms_dict = {}

def model_registered(sender, **kwargs):
    if sender is Model:
        return
    for parent in sender.__bases__:
        model_registered(parent)
    if sender not in perms_dict:
        perms_dict[sender] = CerberusModelPermission(cls=sender)
        # build inherited objects here
        for parent in sender.__bases__:
            if parent is Model:
                continue
            for p in perms_dict[parent].object_perms.keys():
                perms_dict[sender].object_perms[p] = perms_dict[parent].object_perms[p]
                if not sender._meta.abstract and perms_dict[sender].object_perms[p].abstract:
                    perms_dict[sender].object_perms[p] = perms_dict[sender].object_perms[p].clone_non_abstract(sender)
            for p in perms_dict[parent].class_perms.keys():
                perms_dict[sender].class_perms[p] = perms_dict[parent].class_perms[p]
                if not sender._meta.abstract and perms_dict[sender].class_perms[p].abstract:
                    perms_dict[sender].class_perms[p] = perms_dict[sender].object_perms[p].clone_non_abstract(sender)
        # build this model's dictionary here
        if hasattr(sender, '_meta') and hasattr(sender._meta, 'cerberus'):
            if 'object' in sender._meta.cerberus:
                for p in sender._meta.cerberus['object']:
                    perms_dict[sender].object_perms[p[0]] = CerberusPermission(
                        cls=sender, codename=p[0],
                        text=p[1], description=p[2])
                if hasattr(sender._meta, 'abstract') and sender._meta.abstract:
                    perms_dict[sender].object_perms[p[0]].abstract = True
            if 'class' in sender._meta.cerberus:
                for p in sender._meta.cerberus['class']:
                    perms_dict[sender].class_perms[p[0]] = CerberusPermission(
                        cls=sender, codename=p[0],
                        text=p[1], description=p[2])
                if hasattr(sender._meta, 'abstract') and sender._meta.abstract:
                    perms_dict[sender].class_perms[p[0]].abstract = True

class_prepared.connect(model_registered)

def get_perm_content_type(obj, perm):
    """
    This will return the ContentType number the provided permission is
    defined on.

    For example, if the 'pet' permission is defined on Animal,
    and you pass a Dog instance,
    this function will return the ContentType object of Animal.
    This means if you needed to list all Animal objects the user can
    'pet', you can do it in very few queries.
    """
    if isinstance(obj, Model):
        return ContentType.objects.get_for_model(
                perms_dict[obj.__class__].object_perms[perm].cls    
            )
    elif issubclass(obj, Model):
        return ContentType.objects.get_for_model(
                perms_dict[obj].class_perms[perm].cls
            )
    return None

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

def set_perm(self, permission, obj_or_cls):
    content_type = get_perm_content_type(obj_or_cls, permission)
    if isinstance(obj_or_cls, Model):
        if isinstance(self, User):
            pmo = models.UserObjectPermission(user=self, codename=permission, content_type=content_type, object_pk=obj_or_cls.pk)
        elif isinstance(self, Group):
            pmo = models.GroupObjectPermission(group=self, codename=permission, content_type=content_type, object_pk=obj_or_cls.pk)
        else:
            raise ValueError("First argument must be User or Group object.")
    elif issubclass(obj_or_cls, Model):
        if isinstance(self, User):
            pmo = models.UserClassPermission(user=self, codename=permission, content_type=content_type)
        elif isinstance(self, Group):
            pmo = models.GroupClassPermission(group=self, codename=permission, content_type=content_type)
        else:
            raise ValueError("First argument must be a User or Group object.")
    else:
        raise ValueError("Set permission must take a model class or instance as second argument")
    pmo.save()
    return True

def _remove_perm(self, permission, obj_or_cls):
    if isinstance(obj_or_cls, Model):
        content_type = ContentType.objects.get_for_model(obj_or_cls.__class__)
        if isinstance(self, User):
            pmo = models.UserObjectPermission.objects.get(user=self, codename=permission, content_type=content_type, object_pk=obj_or_cls.pk)
        elif isinstance(self, Group):
            pmo = models.GroupObjectPermission.objects.get(group=self, codename=permission, content_type=content_type, object_pk=obj_or_cls.pk)
        else:
            raise ValueError("First argument must be a User or Group object.")
    elif issubclass(obj_or_cls, Model):
        content_type = ContentType.objects.get_for_model(obj_or_cls)
        if isinstance(self, User):
            pmo = models.UserClassPermission.objects.get(user=self, codename=permission, content_type=content_type)
        elif isinstance(self, Group):
            pmo = models.GroupClassPermission.objects.get(group=self, codename=permission, content_type=content_type)
        else:
            raise ValueError("First argument must be a User or Group object.")
    else:
        raise ValueError("Remove permission must take a model class or instance as second argument")
    pmo.delete()
    return True

def __extract_codenames(values):
    codenames = set()
    for obj in values:
        codenames.add(obj['codename'])
    return codenames

def has_perm(self, obj, perm):
    content_type = get_perm_content_type(obj, perm) 
    if isinstance(obj, Model):
        if models.UserObjectPermission.objects.filter(content_type=content_type).filter(object_pk=obj.pk).filter(user=self).filter(codename=perm).exists():
            return True
    if models.UserClassPermission.objects.filter(content_type=content_type).filter(user=self).filter(codename=perm).exists():
        return True
    return False

def get_perms(self, obj):
    """
    Get perms will return all permission codenames on an object or class.

    This function is relatively expensive and has_perm should be used
    when possible.
    """
    response = set()
    if isinstance(obj, Model):
        content_type = ContentType.objects.get_for_model(obj.__class__)
        user_perms = models.UserObjectPermission.objects.filter(content_type=content_type).filter(object_pk=obj.pk).filter(user=self).values('codename')
        response = response.union(__extract_codenames(user_perms))
    elif issubclass(obj, Model):
        content_type = ContentType.objects.get_for_model(obj)
    user_cls_perms = models.UserClassPermission.objects.filter(content_type=content_type).filter(user=self).values('codename')
    response = response.union(__extract_codenames(user_cls_perms))
    return response

setattr(User, 'set_perm', set_perm)
setattr(Group, 'set_perm', set_perm)
setattr(User, 'remove_perm', _remove_perm)
setattr(Group, 'remove_perm', _remove_perm)
setattr(User, 'get_perms', get_perms)
setattr(Group, 'get_perms', get_perms)

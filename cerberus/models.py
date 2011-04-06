from django.db import models
from django.contrib.auth.models import Permission, PermissionManager
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _

class ObjectPermissionBase(models.Model):
    codename = models.CharField(_('codename'), max_length=100)
    content_type = models.ForeignKey(ContentType)
    object_pk = models.CharField(_('object ID'), max_length=255)
    content_object = generic.GenericForeignKey(ct_field="content_type", fk_field="object_pk")
    class Meta:
        abstract = True

class UserObjectPermission(ObjectPermissionBase):
    user = models.ForeignKey(User)

class GroupObjectPermission(ObjectPermissionBase):
    group = models.ForeignKey(Group)

class ClassPermissionBase(models.Model):
    codename = models.CharField(_('codename'), max_length=100)
    content_type = models.ForeignKey(ContentType)
    class Meta:
        abstract = True
 
class UserClassPermission(ClassPermissionBase):
    user = models.ForeignKey(User)

class GroupClassPermission(ClassPermissionBase):
    group = models.ForeignKey(Group)

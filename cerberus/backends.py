import logging
logging.basicConfig(filename="/home/www/cerberuslog.log", level=logging.DEBUG)

from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend

import cerberus
import models

class CerberusBackend(object):
    supports_object_permissions = True
    supports_anonymous_user = False

    def authenticate(self, username=None, password=None):
        return None

    def has_perm(self, user_obj, perm, obj=None):
        """
        This will return True if user has the provided permission
        """
        if not obj:
            return False

        if not user_obj.is_authenticated():
            return False

        if user_obj.is_superuser:
            return True
        
        logging.debug("Requested permission is: " + str(perm) + " on obj " + str(obj)) 
        permissions = cerberus.get_perms(user_obj, obj)
        return perm in permissions

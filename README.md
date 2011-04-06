### Cerberus

django-cerberus intends to allow for per-object permissions for Django.

The general ideas are:

- Permissions should work in inheritance. Perms defined on base classes should exist on their children.
- Permissions can be defined on a per-object or class basis.
- If the same permission codename is defined as both as per-object and class permission, and a user has the class permission, a user.has_perm('perm', instance) should also return true.

### Usage

TODO




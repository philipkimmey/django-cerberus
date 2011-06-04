### Cerberus

django-cerberus intends to allow for per-object permissions for Django.

The general ideas are:

- Permissions should work in inheritance. Perms defined on base classes should exist on their children.
- Permissions can be defined on a per-object or class basis.
- If the same permission codename is defined as both as per-object and class permission, and a user has the class permission, a user.has_perm('perm', instance) should also return true.

### Usage

(These examples are also in tests.py)

```python
class Animal(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        cerberus = {
            'object': (
                ("pet", "Pet", "The user can pet this animal."),
            ),
            'class': (
                ("pet", "Pet", "The user can pet all animals."),
            )
        }

>>> user = User.objects.create_user('john', 'john@test.com', 'testpw')
>>> user.save()
>>> animal = Animal(name="Fido")
>>> animal.save()
>>> user.has_perm('pet', animal)
False
>>> user.set_perm('pet', animal)
>>> user.has_perm('pet', animal)
True
```

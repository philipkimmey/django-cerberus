from django.db import models
from django.test import TestCase

from django.contrib.auth.models import User
from django.contrib.auth.models import Group

"""
Perform basic tests & normal inheritance
"""

class BasicAnimal(models.Model):
    class Meta:
        cerberus = {
            'object': (
                ("pet", "Pet", "The user can eat this animal."),
            ),
            'class': (
                ("pet", "Pet", "The user can eat all animals."),
            )
        }
    name = models.CharField(max_length=100)

class BasicTest(TestCase):
    def setUp(self):
        self.fido = BasicAnimal(name="fido")
        self.fido.save()

        self.user = User.objects.create_user('testme', 'testing@test.com', 'testingpw')
        self.user.save()
    def test_basic_user_permissions(self):
        self.assertFalse(self.user.has_perm('pet', self.fido))
        self.user.set_perm('pet', self.fido)
        self.assertTrue(self.user.has_perm('pet', self.fido))
        self.user.remove_perm('pet', self.fido)
        self.assertFalse(self.user.has_perm('pet', self.fido))

class BasicDog(BasicAnimal):
    breed = models.CharField(max_length=100)

class InheritanceTest(TestCase):
    def setUp(self):
        self.fido = BasicDog(name="fido", breed="Golden Lab")
        self.fido.save()

        self.user = User.objects.create_user('testme', 'testing@test.com', 'testingpw')
        self.user.save()
    def test_inheritance(self):
        self.assertFalse(self.user.has_perm('pet', self.fido))
        self.user.set_perm('pet', self.fido)
        self.assertTrue(self.user.has_perm('pet', self.fido))

"""
Perform tests on abstract inheritance
"""

class AbstractAnimal(models.Model):
    class Meta:
        cerberus = (
            ("pet", "Pet", "The user can eat this animal."),
            ("eat", "Eat", "The user is allowed to eat this animal."),
        )
        abstract = True
    name = models.CharField(max_length=100)

class AbstractInheritedDog(AbstractAnimal):
    breed = models.CharField(max_length=100)

class AbstractInheritanceTest(TestCase):
    def setUp(self):
        self.fido = AbstractInheritedDog(name="fido", breed="golden lab")
        self.fido.save()

        self.user = User.objects.create_user('testme', 'testing@test.com', 'testingpw')
        self.user.save()
    def test_abstract_inheritance(self):
        self.assertFalse(self.user.has_perm('pet', self.fido))
        self.user.set_perm('pet', self.fido)
        self.assertTrue(self.user.has_perm('pet', self.fido))

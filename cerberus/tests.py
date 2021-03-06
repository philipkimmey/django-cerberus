from django.db import models
from django.test import TestCase

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.contrib.auth.models import Group

import cerberus

"""
Perform basic tests & normal inheritance.
"""

class BasicAnimal(models.Model):
    class Meta:
        cerberus = {
            'object': (
                ("pet", "Pet", "The user can pet this animal."),
            ),
            'class': (
                ("pet", "Pet", "The user can pet all animals."),
                ("eat", "Eat", "The user can eat all animals."),
            )
        }
    name = models.CharField(max_length=100)

class BasicUserTest(TestCase):
    """
    Tests for user permissions on models
    with no inheritance.
    """
    def setUp(self):
        self.fido = BasicAnimal(name="fido")
        self.fido.save()

        self.user = User.objects.create_user('testme', 'testing@test.com', 'testingpw')
        self.user.save()
    def test_basic_user_permissions(self):
        self.assertFalse(self.user.has_perm('pet', self.fido))
        self.assertFalse(self.user.has_perm('pet'))
        self.user.set_perm('pet', self.fido)
        self.assertTrue(self.user.has_perm('pet', self.fido))
        self.user.remove_perm('pet', self.fido)
        self.assertFalse(self.user.has_perm('pet', self.fido))
        self.assertFalse(self.user.has_perm('eat', self.fido.__class__))
    def test_user_class_permissions(self):
        self.assertFalse(self.user.has_perm('pet', self.fido))
        self.assertFalse(self.user.has_perm('pet', self.fido.__class__))
        self.user.set_perm('pet', BasicAnimal)
        self.assertTrue(self.user.has_perm('pet', self.fido))
        self.assertTrue(self.user.has_perm('pet', self.fido.__class__))
        self.assertFalse(self.user.has_perm('eat', self.fido.__class__))
        self.user.set_perm('eat', BasicAnimal)
        self.assertTrue(self.user.has_perm('eat', self.fido.__class__))

class BasicGroupTest(TestCase):
    """
    Tests for group permissions on models
    with no inheritance.
    """
    def setUp(self):
        self.fido = BasicAnimal(name="fido")
        self.fido.save()

        self.user1 = User.objects.create_user('testme', 'testing@test.com', 'testingpw')
        self.user1.save()

        self.user2 = User.objects.create_user('testme2', 'testing2@test.com', 'testingpw')
        self.user2.save()

        self.group = Group(name='testgroup')
        self.group.save()
    def test_basic_group_permissions(self):
        self.assertFalse(self.user1.has_perm('pet', self.fido))
        self.group.set_perm('pet', self.fido)
        self.assertFalse(self.user1.has_perm('pet', self.fido))
        self.user1.groups.add(self.group)
        self.assertTrue(self.user1.has_perm('pet', self.fido))
        self.assertFalse(self.user2.has_perm('pet', self.fido))
        self.user2.groups.add(self.group)
        self.assertTrue(self.user2.has_perm('pet', self.fido))
        self.assertTrue(self.group.has_perm('pet', self.fido))
    def test_group_class_permissions(self):
        self.assertFalse(self.user1.has_perm('pet', self.fido))
        self.assertFalse(self.user2.has_perm('pet', self.fido))
        self.group.set_perm('pet', self.fido.__class__)
        self.assertFalse(self.user1.has_perm('pet', self.fido))
        self.assertFalse(self.user1.has_perm('pet', self.fido.__class__))
        self.user1.groups.add(self.group)
        self.assertTrue(self.user1.has_perm('pet', self.fido))
        self.assertTrue(self.user1.has_perm('pet', self.fido.__class__))
        self.assertFalse(self.user2.has_perm('pet', self.fido))
        self.assertFalse(self.user2.has_perm('pet', self.fido.__class__))
        # test behavior of perm only defined on class
        self.assertFalse(self.user1.has_perm('eat', self.fido))
        self.assertFalse(self.user1.has_perm('eat', self.fido.__class__))
        self.assertFalse(self.user2.has_perm('eat', self.fido))
        self.assertFalse(self.user2.has_perm('eat', self.fido.__class__))
        self.group.set_perm('eat', self.fido.__class__)
        self.assertTrue(self.user1.has_perm('eat', self.fido))
        self.assertTrue(self.user1.has_perm('eat', self.fido.__class__))
        self.assertFalse(self.user2.has_perm('eat', self.fido))
        self.assertFalse(self.user2.has_perm('eat', self.fido.__class__))

class BasicDog(BasicAnimal):
    breed = models.CharField(max_length=100)

class UserInheritanceTest(TestCase):
    def setUp(self):
        self.fido = BasicDog(name="fido", breed="Golden Lab")
        self.fido.save()

        self.user = User.objects.create_user('testme', 'testing@test.com', 'testingpw')
        self.user.save()
    def test_get_perm_content_type(self):
        self.assertEqual(ContentType.objects.get_for_model(BasicAnimal),
            cerberus.get_perm_content_type(BasicDog, 'pet'))
    def test_inheritance(self):
        self.assertFalse(self.user.has_perm('pet', self.fido))
        self.user.set_perm('pet', self.fido)
        self.assertTrue(self.user.has_perm('pet', self.fido))
    def test_class_inheritance(self):
        self.user.set_perm('pet', BasicDog)
        self.assertTrue(self.user.has_perm('pet', self.fido))
    def test_superclass_permissions(self):
        self.user.set_perm('pet', BasicAnimal)
        self.assertTrue(self.user.has_perm('pet', self.fido))

class GroupInheritanceTest(TestCase):
    def setUp(self):
        self.fido = BasicDog(name="fido", breed="Golden Lab")
        self.fido.save()

        self.user1 = User.objects.create_user('testme1',
                'testing@test.com', 'testingpw')
        self.user1.save()

        self.user2 = User.objects.create_user('testme2',
                'testing2@test.com', 'testingpw')
        self.user2.save()
        
        self.group = Group(name='testgroup')
        self.group.save()
    def test_group_inheritance(self):
        self.assertFalse(self.user1.has_perm('pet', self.fido))
        self.assertFalse(self.group.has_perm('pet', self.fido))

"""
Perform tests on abstract inheritance
"""

class AbstractAnimal(models.Model):
    class Meta:
        cerberus = {
            'object': (
                ("pet", "Pet", "The user can pet this animal."),
            ),
            'class': (
                ("pet", "Pet", "The user can pet all animals."),
            )
        }
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

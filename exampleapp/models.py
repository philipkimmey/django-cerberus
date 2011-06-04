from django.db import models

class Animal(models.Model):
    class Meta:
        cerberus = {
            'object': (
                ("pet", "Pet", "Can pet this animal."),
                ("rename", "Rename", "Can rename this animal"),
            ),
            'class': (
                ("pet", "Pet", "Can pet all animals."),
                ("play", "Play", "Can play with all animals."),
                ("eat", "Eat", "Can eat all animals."),
            )
        }
    name = models.CharField(max_length=100)
    def __unicode__(self):
        return self.name

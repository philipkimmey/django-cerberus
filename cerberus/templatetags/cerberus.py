from django import template
from django.template.defaultfilters import register

register = template.Library()

class CerberusNode(template.Node):
    def __init__(self, user, obj, context_var):
        self.user = template.Variable(user)
        self.obj = template.Variable(obj)
        self.context_var = context_var

    def render(self, context):
        pass

@register.filter(name='lookup')
def lookup(dict, index):
    if index in dict:
        return dict[index]
    return ''

from django import template

register = template.Library()

class CerberusNode(template.Node):
    def __init__(self, user, obj, context_var):
        self.user = template.Variable(user)
        self.obj = template.Variable(obj)
        self.context_var = context_var

    def render(self, context):
        pass

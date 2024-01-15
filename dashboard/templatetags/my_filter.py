from django import template

register = template.Library()


@register.filter
def get_attr(value):
    return dir(value)

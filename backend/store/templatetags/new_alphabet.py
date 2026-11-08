from django import template
from store.text import new_uzbek_alphabet

register = template.Library()


@register.filter
def newlatin(value):
    return new_uzbek_alphabet(value)

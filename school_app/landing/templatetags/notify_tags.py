from django import template

register = template.Library()


@register.filter
def get_item(mapping, key):
    """{{ counts|get_item:obj.pk }}: look up a value by key, '' when missing."""
    return mapping.get(key, "") if mapping else ""

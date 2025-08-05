from django import template

register = template.Library()

@register.filter(name="replace")
def replace(value: str, args: str) -> str:
    """
    Usage in template:
        {{ some_text|replace:"old,new" }}
    """
    old, new = args.split(",", 1)
    return value.replace(old, new)

@register.filter(name="replaceexe")
def replaceexe(value: str) -> str:
    """
    Usage in template:
        {{ some_text|replace:"old,new" }}
    """
    return value.replace(".exe", "").lower()
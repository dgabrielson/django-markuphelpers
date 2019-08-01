"""
Set of "markup" template filters for Django.  These filters transform plain text
markup syntaxes to HTML; currently there is support for:

    * reStructuredText, which requires docutils from http://docutils.sf.net/
    
Note also security advisory:
    https://www.djangoproject.com/weblog/2015/apr/21/docutils-security-advisory/
"""
from __future__ import unicode_literals, print_function

from django import template
from django.conf import settings
from django.utils.encoding import smart_bytes, force_text
from django.utils.safestring import mark_safe

from docutils.core import publish_parts


register = template.Library()


@register.filter(is_safe=True)
def restructuredtext(value):
    """
    TODO: errors?
    """
    filter_settings = {
        'raw_enabled': False,
        'file_insertion_enabled': False,
        'initial_header_level': 2,
    }
    filter_settings.update(getattr(settings, 'RESTRUCTUREDTEXT_FILTER_SETTINGS', {}))
    parts = publish_parts(
        source=smart_bytes(value),
        writer_name="html",
        settings_overrides=filter_settings,
    )
    return mark_safe(force_text(parts["body"]))


"""
Forms for the markuphelpers application.
"""
from __future__ import unicode_literals, print_function
#######################################################################

from types import MethodType

import django   # for VERSION check
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms.utils import flatatt
from django.utils.encoding import force_text
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from django.contrib.staticfiles.storage import staticfiles_storage



###############################################################

def _restructuredtext_field_clean(field_name, warning_fail):
    """
    Do the ReStructuredText validation on a particular field.
    """
    def _inner_rst_clean(self):
        try:
            from docutils.core import publish_parts
            from docutils.utils import SystemMessage
        except ImportError:
            raise ValidationError('Cannot handle reStructuredText; is docutils installed?')

        value = self.cleaned_data[field_name]

        docutils_settings = getattr(settings,
                                    "RESTRUCTUREDTEXT_FILTER_SETTINGS", {})
        docutils_settings['traceback'] = True
        if warning_fail:
            docutils_settings['halt_level'] = 2 # warnings
        else:
            docutils_settings['halt_level'] = 3 # errors

        try:
            parts = publish_parts(source=force_text(value),
                                  writer_name="html4css1",
                                  settings_overrides=docutils_settings)
        except SystemMessage as sysmsg:
            raise ValidationError(self._rst_msg_rewrite(str(sysmsg)))
        except AttributeError:
            raise ValidationError("Critical reStructuredText Error; check things like links or references")
        return value
    return _inner_rst_clean


###############################################################

class ReStructuredTextFormMixin(object):
    """
    Use this mixin when you have a field to be validated as ReStructuredText,
    i.e., you use {{ object.field|restructuredtext }} in your templates.

    Usage, in your ModelForm, set the following class attributes:
    | restructuredtext_fields = ( (field_name, warning_fail), ... )


    ``restructuredtext_fields`` is a list containing the names of the
    fields that you want to validate and a boolean flag indicating
    whether or not warnings should cause validation failure for that field.

    NOTE: If you need to supply your own ``clean_field_name()`` function,
    You need to call ``_restructuredtext_field_clean()`` yourself.
    """
    restructuredtext_fields = []


    def _rst_msg_rewrite(self, message):
        """
        Rewrite a standard docutils SystemMessage from, e.g.,
        <string>:16: (ERROR/3) Unexpected indentation.
        to
        reStructuredText Error (line 16) Unexpected indentation.
        """
        parts = message.split(':', 2)
        if len(parts) != 3:
            return message
        string, line, text = parts
        if string != '<string>':
            return message
        lvl, text = text.split(') ', 1)
        level = lvl.strip().lstrip('(').split('/')[0].title()
        return "reStructuredText {level}, line {line}: {text}".format(
                                    level=level, line=line, text=text)


    def __init__(self, *args, **kwargs):
        """
        Construct cleaner functions.
        (As long as they don't already exist.)
        """
        for field, wfail in self.restructuredtext_fields:
            f_name = 'clean_' + field
            if not hasattr(self, f_name):
                f = _restructuredtext_field_clean(field, wfail)
                setattr(self, f_name, MethodType(f, self))
        return super(ReStructuredTextFormMixin, self).__init__(*args, **kwargs)


###############################################################

class LinedTextAreaMediaMixin(object):

    class Media:
        css = {'all': (
                    staticfiles_storage.url("markuphelpers/css/jquery-linedtextarea.css"),
                )}
        js = (
                staticfiles_storage.url("admin/js/vendor/jquery/jquery.min.js"),
                staticfiles_storage.url("admin/js/jquery.init.js"),
                staticfiles_storage.url("markuphelpers/js/jquery-linedtextarea.js"),
            )

###############################################################

class LinedTextareaWidget(LinedTextAreaMediaMixin, forms.Textarea):
    """
    Provide a widget for editing markup text.
    """
    template_name = 'markuphelpers/forms/widgets/linedtextarea.html'

    def __init__(self, attrs=None, wrap_p=True, auto_script=True):
        default_attrs = {'cols': '80', 'rows': '24', 'class': 'linedTextArea'}
        if attrs:
            default_attrs.update(attrs)
        self.wrap_p = wrap_p    # make nested divs from jQuery work with django admin
        self.auto_script = auto_script
        return super(LinedTextareaWidget, self).__init__(default_attrs)


    @classmethod
    def activation_js(cls, selector=None):
        if selector is None:
            selector = '.linedTextArea'
        return mark_safe('''
(function($){{
    if ( $('{selector}').is(':visible') ) {{
        $('{selector}').linedtextarea();
    }}
}})(django.jQuery);
'''.format(selector=selector))


    def get_script(self, attrs):
        selector = None
        if 'id' in attrs:
            selector = '#' + attrs['id']
        else:
            selector = '.' + attrs['class']

        if self.auto_script:
            script = '<script type="text/javascript">' + self.activation_js(selector) + u'</script>'
        else:
            script = ''
        return mark_safe(script)


    def get_context(self, *arg, **kwargs):
        context = super(LinedTextareaWidget, self).get_context(*arg, **kwargs)
        context['script'] = self.get_script(context['widget']['attrs'])
        context['wrap_p'] = self.wrap_p
        return context


    if django.VERSION < (1,11):
        def render(self, name, value, attrs=None):
            if value is None: value = ''
            final_attrs = self.build_attrs(attrs, name=name)

            open_tag = '<textarea' + flatatt(final_attrs) + '>'
            close_tag = '</textarea>'
            if self.wrap_p:
                open_tag = '<p>' + open_tag
                close_tag = close_tag + '</p>'

            script = self.get_script(final_attrs)
            content = conditional_escape(force_text(value))
            return mark_safe(open_tag + content + close_tag + script)




###############################################################
###############################################################

## Example usage:

# from markuphelpers.forms import ReStructuredTextFormMixin, LinedTextareaWidget

# class ShoutForm(ReStructuredTextFormMixin, forms.ModelForm):
#
#     restructuredtext_fields = [ ('content', True), ]
#
#     class Meta:
#         model = Shout
#         widgets = {
#                 'content': LinedTextareaWidget,
#             }
#

###############################################################

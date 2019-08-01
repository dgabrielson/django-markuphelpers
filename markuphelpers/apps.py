from __future__ import unicode_literals, print_function
#########################################################################

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

#########################################################################

class MarkupHelpersConfig(AppConfig):
    name = "markuphelpers"
    verbose_name = _("Markup Helpers")

    def ready(self):
        """
        Any app specific startup code, e.g., register signals,
        should go here.
        """

#########################################################################

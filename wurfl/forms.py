from django import forms
from django.utils.translation import ugettext_lazy as _


class WurflImportForm(forms.Form):
    xml_file = forms.FileField(label=_('XML file'), required=True, help_text=_('Please ensure that the file is well XML formated'))

class WurflSearchForm(forms.Form):
    user_agent = forms.CharField(label=_('User Agent'), required=True)
    test = forms.BooleanField(label=_('Match algoritm'), required=False, help_text=_("If selected, use the internal algoritm based on 'Levenshtein' to try to match the User-Agent"))
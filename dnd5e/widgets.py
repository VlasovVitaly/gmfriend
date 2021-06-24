import django.forms.widgets as widgets


class AbilityListBoxSelect(widgets.SelectMultiple):
    template_name = 'dnd5e/widgets/ability_list_box.html'
    option_template_name = 'dnd5e/widgets/ability_list_box_option.html'

    class Media:
        css = {'all': ('css/ability_listbox.css',)}
        js = ('js/ability_listbox.js',)
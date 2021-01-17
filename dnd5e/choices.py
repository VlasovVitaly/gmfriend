from django.apps import apps
from .forms import SelectToolProficiency, SelectFeatureForm

dnd5e_app = apps.app_configs['dnd5e']


class PROF_TOOLS_001:
    form_class = SelectToolProficiency
    queryset = dnd5e_app.get_model('tool').objects.filter(category=15)  # Gamble
    selection_limit = 1

    def __init__(self, character):
        self.character = character

    def get_form(self, request, character):
        return self.form_class(data=request.POST or None, limit=self.selection_limit, queryset=self.queryset)

    def apply_data(self, data):
        for tool in data['tools']:
            self.character.tools_proficiency.add(tool)


class PROF_TOOLS_002(PROF_TOOLS_001):
    queryset = dnd5e_app.get_model('tool').objects.filter(category=10)  # Musical


class PROF_TOOLS_003(PROF_TOOLS_001):
    queryset = dnd5e_app.get_model('tool').objects.filter(category=5)  # Artisian


class CLASS_WAR_001:
    form_class = SelectFeatureForm
    queryset = dnd5e_app.get_model('feature').objects.filter(group='fight_style')

    def __init__(self, character):
        self.character = character

    def get_form(self, request, character):
        return self.form_class(data=request.POST or None, queryset=self.queryset)

    def apply_data(self, data):
        self.character.features.add(data['feature'])


ALL_CHOICES = {
    'PROF_TOOLS_001': PROF_TOOLS_001,
    'PROF_TOOLS_002': PROF_TOOLS_002,
    'PROF_TOOLS_003': PROF_TOOLS_003,
    'CLASS_WAR_001': CLASS_WAR_001,
}

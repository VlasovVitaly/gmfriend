from django.apps import apps
from .forms import SelectToolProficiency, SelectFeatureForm, SelectSubclassForm, SelectAbilityAdvanceForm

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
        CharacterFeature = dnd5e_app.get_model('characterfeature')
        CharacterFeature.objects.create(character=self.character, feature=data['feature'])


class CLASS_ROG_001:
    queryset = dnd5e_app.get_model('subclass').objects.filter(parent__orig_name='Rogue')
    form_class = SelectSubclassForm

    def __init__(self, character):
        self.character = character

    def get_form(self, request, character):
        return self.form_class(data=request.POST or None, queryset=self.queryset)

    def apply_data(self, data):
        self.character.subclass = data['subclass']
        self.character.save(update_fields=['subclass'])

        self.character._apply_subclass_advantages(3)


class CHAR_ADVANCE_001:
    form_class = SelectAbilityAdvanceForm

    def __init__(self, character):
        self.character = character

    def get_form(self, request, character):
        return self.form_class(data=request.POST or None)

    def apply_data(self, data):
        print("apply", data)


class POST_FEAT_001:
    def apply(self, character):
        wisdom = character.abilities.get(ability__orig_name='Wisdom')
        wisdom.saving_trow_proficiency = True
        wisdom.save(update_fields=['saving_trow_proficiency'])


ALL_CHOICES = {
    'CHAR_ADVANCE_001': CHAR_ADVANCE_001,
    'PROF_TOOLS_001': PROF_TOOLS_001,
    'PROF_TOOLS_002': PROF_TOOLS_002,
    'PROF_TOOLS_003': PROF_TOOLS_003,
    'CLASS_WAR_001': CLASS_WAR_001,
    'CLASS_ROG_001': CLASS_ROG_001,
    'POST_FEAT_001': POST_FEAT_001,
}
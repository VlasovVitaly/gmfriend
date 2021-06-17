from dnd5e.models import Character
from django.apps import apps
from .forms import SelectToolProficiency, SelectFeatureForm, SelectSubclassForm, SelectAbilityAdvanceForm, SelectCompetenceForm

dnd5e_app = apps.app_configs['dnd5e']


class DummyValidForm:
    def is_valid():
        return True


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
            dnd5e_app.get_model('charactertoolproficiency').objects.create(character=self.character, tool=tool)


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

        self.character._apply_subclass_advantages(3)  # Rogue select arhtype on level 3


class CLASS_ROG_002:
    template = 'dnd5e/adventures/include/choices/rogue_002.html'
    form_class = SelectCompetenceForm

    def __init__(self, character):
        self.character = character

    def get_form(self, request, character):
        return self.form_class(data=request.POST or None, queryset=character.skills.filter(competence=False, proficiency=True))

    def apply_data(self, data):
        data['skills'].update(competence=True)
        if data['tool']:
            data['tool'].competence = True
            data['tool'].save(update_fields=['competence'])


class CHAR_ADVANCE_001:
    template = 'dnd5e/adventures/include/choices/advance_001.html'
    form_class = SelectAbilityAdvanceForm

    def __init__(self, character):
        self.character = character

    def get_form(self, request, character):
        return self.form_class(
            data=request.POST or None, files=request.FILES or None,
            queryset=dnd5e_app.get_model('characterabilities').objects.filter(character=character)
        )

    def apply_data(self, data):
        abilities = data['abilities']
        if len(abilities) == 2:
            abilities.increase_value(1)
        elif len(abilities) == 1:
            abilities.increase_value(2)


class POST_FEAT_001:
    def get_form(self, request, character):
        return DummyValidForm()

    def apply(self, character):
        wisdom = character.abilities.get(ability__orig_name='Wisdom')
        wisdom.saving_trow_proficiency = True
        wisdom.save(update_fields=['saving_trow_proficiency'])


class POST_FEAT_002:
    def apply(self, character):
        char_choices = dnd5e_app.get_model('characteradvancmentchoice')
        competence_choice = dnd5e_app.get_model('advancmentchoice').objects.get(code='CLASS_ROG_002')
        reason_obj = dnd5e_app.get_model('class').objects.get(name='Плут')

        char_choices.objects.get_or_create(
            character=character, choice=competence_choice,
            defaults={'reason': reason_obj}
        )


ALL_CHOICES = {
    'CHAR_ADVANCE_001': CHAR_ADVANCE_001,
    'PROF_TOOLS_001': PROF_TOOLS_001,
    'PROF_TOOLS_002': PROF_TOOLS_002,
    'PROF_TOOLS_003': PROF_TOOLS_003,
    'CLASS_WAR_001': CLASS_WAR_001,
    'CLASS_ROG_001': CLASS_ROG_001,
    'CLASS_ROG_002': CLASS_ROG_002,
    'POST_FEAT_001': POST_FEAT_001,
    'POST_FEAT_002': POST_FEAT_002,
}
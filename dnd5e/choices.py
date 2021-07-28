from django.apps import apps

from .forms import (
    AddCharLanguageFromBackground, AddCharSkillProficiency, CharacterBackgroundForm, MasterMindIntrigueSelect,
    SelectAbilityAdvanceForm, SelectCompetenceForm, SelectFeatureForm, SelectSubclassForm, SelectToolProficiency
)

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
            dnd5e_app.get_model('charactertoolproficiency').objects.create(character=self.character, tool=tool)


class PROF_TOOLS_002(PROF_TOOLS_001):
    queryset = dnd5e_app.get_model('tool').objects.filter(category=10)  # Musical


class PROF_TOOLS_003(PROF_TOOLS_001):
    queryset = dnd5e_app.get_model('tool').objects.filter(category=5)  # Artisian


class CLASS_WAR_001:
    """ Боевой стиль воина """
    form_class = SelectFeatureForm
    queryset = dnd5e_app.get_model('feature').objects.filter(group='fight_style')

    def __init__(self, character):
        self.character = character

    def get_form(self, request, character):
        exclude_feats = self.character.features.filter(feature__group='fight_style').values_list('feature_id')  # Already know
        return self.form_class(data=request.POST or None, queryset=self.queryset.exclude(id__in=exclude_feats))

    def apply_data(self, data):
        CharacterFeature = dnd5e_app.get_model('characterfeature')
        CharacterFeature.objects.create(character=self.character, feature=data['feature'])


class CLASS_WAR_002:
    """ Воинский архетип """
    queryset = dnd5e_app.get_model('subclass').objects.filter(parent__orig_name='Fighter')
    form_class = SelectSubclassForm

    def __init__(self, character):
        self.character = character

    def get_form(self, request, character):
        return self.form_class(data=request.POST or None, queryset=self.queryset)

    def apply_data(self, data):
        self.character.apply_subclass(data['subclass'], 3)  # Fighter select arhtype on level 3


class CLASS_ROG_001:
    """ Rogue archtype selection """
    queryset = dnd5e_app.get_model('subclass').objects.filter(parent__orig_name='Rogue')
    form_class = SelectSubclassForm

    def __init__(self, character):
        self.character = character

    def get_form(self, request, character):
        return self.form_class(data=request.POST or None, queryset=self.queryset)

    def apply_data(self, data):
        self.character.apply_subclass(data['subclass'], 3)  # Rogue select arhtype on level 3


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


class CLASS_ROG_003:
    """ Выбор для интригана """
    form_class = MasterMindIntrigueSelect

    def __init__(self, character):
        self.character = character

    def get_form(self, request, character):
        return self.form_class(request.POST or None, character=character)

    def apply_data(self, data):
        _ = dnd5e_app.get_model('charactertoolproficiency').objects.create(
            character=self.character, tool=data['tool']
        )
        for lang in data['languages']:
            self.character.languages.add(lang)


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


class CHAR_ADVANCE_002:
    ''' Выбор мастерства классовых навыков '''
    form_class = AddCharSkillProficiency

    def __init__(self, character):
        self.character = character

    def get_form(self, request, character):
        return self.form_class(
            data=request.POST or None, files=None,
            limit=character.klass.skill_proficiency_limit,
            skills=character.skills.exclude(proficiency=True)
        )

    def apply_data(self, data):
        data['skills'].update(proficiency=True)


class CHAR_ADVANCE_003:
    ''' Выбор языков из прелыстории '''
    form_class = AddCharLanguageFromBackground

    def __init__(self, character):
        self.character = character

    def get_form(self, request, character):
        return self.form_class(
            data=request.POST or None, files=None,
            limit=character.background.known_languages,
            queryset=dnd5e_app.get_model('language').objects.exclude(id__in=character.languages.all().values_list('id'))
        )

    def apply_data(self, data):
        for lang in data['langs']:
            self.character.languages.add(lang)


class CHAR_ADVANCE_004:
    ''' Выбор деталей предыистории '''
    form_class = CharacterBackgroundForm
    template = 'dnd5e/adventures/include/choices/advance_004.html'

    def __init__(self, character):
        self.character = character

    def get_form(self, request, character):
        return self.form_class(
            data=request.POST or None, files=None,
            background=character.background
        )

    def apply_data(self, data):
        print(data)


class POST_FEAT_001:
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


class POST_FEAT_003(POST_FEAT_001):
    """ Убийца """
    def apply(self, character):
        char_tools = dnd5e_app.get_model('charactertoolproficiency')
        for tool in dnd5e_app.get_model('tool').objects.filter(name__in=['Инструменты отравителя', 'Набор для грима']):
            _, _ = char_tools.objects.get_or_create(character=character, tool=tool)


class POST_FEAT_004:
    """ Комбинатор / Интриган """
    def apply(self, character):
        char_tools = dnd5e_app.get_model('charactertoolproficiency')
        for tool in dnd5e_app.get_model('tool').objects.filter(name__in=['Набор для фальсификации', 'Набор для грима']):
            _, _ = char_tools.objects.get_or_create(character=character, tool=tool)

        char_choices = dnd5e_app.get_model('characteradvancmentchoice')
        char_choices.objects.create(
            character=character,
            choice=dnd5e_app.get_model('advancmentchoice').objects.get(code='CLASS_ROG_003'),
            reason=dnd5e_app.get_model('subclass').objects.get(name='Комбинатор')
        )


class POST_FEAT_005:
    """ Скаут / Выживальщик """
    def apply(self, character):
        character.skills.filter(skill__name__in=('Природа', 'Выживание')).update(proficiency=True)
        # NOTE mb need add extra_bonus to CharacterSkill


class POST_FEAT_006:
    """ Скаут / Превосходная мобильность """
    def apply(self, character):
        # TODO Add speeds to character model
        pass


ALL_CHOICES = {
    'CHAR_ADVANCE_001': CHAR_ADVANCE_001,
    'CHAR_ADVANCE_002': CHAR_ADVANCE_002,
    'CHAR_ADVANCE_003': CHAR_ADVANCE_003,
    'CHAR_ADVANCE_004': CHAR_ADVANCE_004,
    'PROF_TOOLS_001': PROF_TOOLS_001,
    'PROF_TOOLS_002': PROF_TOOLS_002,
    'PROF_TOOLS_003': PROF_TOOLS_003,
    'CLASS_WAR_001': CLASS_WAR_001,
    'CLASS_WAR_002': CLASS_WAR_002,
    'CLASS_ROG_001': CLASS_ROG_001,
    'CLASS_ROG_002': CLASS_ROG_002,
    'CLASS_ROG_003': CLASS_ROG_003,
    'POST_FEAT_001': POST_FEAT_001,
    'POST_FEAT_002': POST_FEAT_002,
    'POST_FEAT_003': POST_FEAT_003,
    'POST_FEAT_004': POST_FEAT_004,
    'POST_FEAT_005': POST_FEAT_005,
    'POST_FEAT_006': POST_FEAT_006,
}
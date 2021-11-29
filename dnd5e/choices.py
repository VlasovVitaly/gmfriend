import re
from django.apps import apps

from dnd5e.models import CharacterToolProficiency

from .forms import (
    AddCharLanguageFromBackground, AddCharSkillProficiency, CharacterBackgroundForm,
    ManeuversSelectForm, MasterMindIntrigueSelect, SelectAbilityAdvanceForm,
    SelectCompetenceForm, SelectFeatureForm, SelectSubclassForm, SelectToolProficiency
)

dnd5e_app = apps.app_configs['dnd5e']
get_model = dnd5e_app.get_model


class CharacterChoice:
    form_class = None
    queryset = None
    selection_limit = None

    def __init__(self, character):
        self.character = character
    
    def get_form(self, request):
        if self.form_class is None: raise AssertionError('Choice formclass is not set')

        form_args = {'data': request.POST or None, 'files': None}

        if self.queryset:
            form_args['queryset'] = self.queryset
        
        if self.selection_limit:
            form_args['limit'] = self.selection_limit

        return self.form_class(**form_args)
    
    def apply_data(self, data):
        raise AssertionError('apply_data is not defined')


class PROF_TOOLS_001(CharacterChoice):
    """ Владение одним игровым набором """
    form_class = SelectToolProficiency
    queryset = get_model('tool').objects.filter(category=15)  # Gamble
    selection_limit = 1

    def apply_data(self, data):
        CharToolsModel = get_model('charactertoolproficiency')
        CharToolsModel.objects.bulk_create(
            CharToolsModel(character=self.character, tool=tool) for tool in data['tools']
        )


class PROF_TOOLS_002(PROF_TOOLS_001):
    """ Владение одним музыкальным инструментом """
    queryset = get_model('tool').objects.filter(category=10)  # Musical


class PROF_TOOLS_003(PROF_TOOLS_001):
    """ Владение одним ремесленным инструментом """
    queryset = get_model('tool').objects.filter(category=5)  # Artisian


class CLASS_WAR_001(CharacterChoice):
    """ Боевой стиль воина """
    form_class = SelectFeatureForm
    queryset = get_model('feature').objects.filter(group='fight_style')

    def get_form(self, request):
        self.queryset = get_model('feature').objects.filter(group='fight_style').exclude(
            id__in=self.character.features.filter(feature__group='fight_style').values_list('feature_id') 
        )

        return super().get_form(request)

    def apply_data(self, data):
        get_model('characterfeature').objects.create(character=self.character, feature=data['feature'])


class CLASS_WAR_002(CharacterChoice):
    """ Воинский архетип """
    queryset = get_model('subclass').objects.filter(parent__orig_name='Fighter')
    form_class = SelectSubclassForm

    def apply_data(self, data):
        self.character.apply_subclass(data['subclass'], 3)  # Fighter select arhtype on level 3


class CLASS_BATTLE_001(CharacterChoice):
    """ Мастер боевых исскуств / Боевое превосходство """
    form_class = ManeuversSelectForm
    
    def apply_data(self, data):
        print("do something")
        return None


class CLASS_ROG_001(CharacterChoice):
    """ Rogue archtype selection """
    queryset = get_model('subclass').objects.filter(parent__orig_name='Rogue')
    form_class = SelectSubclassForm

    def apply_data(self, data):
        self.character.apply_subclass(data['subclass'], 3)  # Rogue select arhtype on level 3


class CLASS_ROG_002(CharacterChoice):
    template = 'dnd5e/adventures/include/choices/rogue_002.html'
    form_class = SelectCompetenceForm

    def get_form(self, request):
        self.queryset = self.character.skills.filter(competence=False, proficiency=True)

        return super().get_form(request)

    def apply_data(self, data):
        data['skills'].update(competence=True)
        if data['tool']:
            data['tool'].competence = True
            data['tool'].save(update_fields=['competence'])


class CLASS_ROG_003(CharacterChoice):
    """ Выбор для интригана """
    form_class = MasterMindIntrigueSelect

    def get_form(self, request):
        return self.form_class(request.POST or None, character=self.character)

    def apply_data(self, data):
        _ = get_model('charactertoolproficiency').objects.create(
            character=self.character, tool=data['tool']
        )
        for lang in data['languages']:
            self.character.languages.add(lang)


class CHAR_ADVANCE_001(CharacterChoice):
    ''' Повышение характеристик '''
    template = 'dnd5e/adventures/include/choices/advance_001.html'
    form_class = SelectAbilityAdvanceForm

    def get_form(self, request):
        self.queryset = get_model('characterabilities').objects.filter(character=self.character)

        return super().get_form(request)

    def apply_data(self, data):
        abilities = data['abilities']

        if len(abilities) == 2:
            abilities.increase_value(1)
        elif len(abilities) == 1:
            abilities.increase_value(2)


class CHAR_ADVANCE_002(CharacterChoice):
    ''' Выбор мастерства классовых навыков '''
    form_class = AddCharSkillProficiency

    def get_form(self, request):
        return self.form_class(
            data=request.POST or None, files=None,
            limit=self.character.klass.skill_proficiency_limit,
            skills=self.character.skills.exclude(proficiency=True)
        )

    def apply_data(self, data):
        data['skills'].update(proficiency=True)


class CHAR_ADVANCE_003(CharacterChoice):
    ''' Выбор языков из предыстории '''
    form_class = AddCharLanguageFromBackground

    def get_form(self, request):
        self.selection_limit = self.character.background.known_languages 
        self.queryset = get_model('language').objects.exclude(
            id__in=self.character.languages.all().values_list('id')
        )

        super().get_form(request)

    def apply_data(self, data):
        for lang in data['langs']:
            self.character.languages.add(lang)


class CHAR_ADVANCE_004(CharacterChoice):
    ''' Выбор деталей предыистории '''
    form_class = CharacterBackgroundForm
    template = 'dnd5e/adventures/include/choices/advance_004.html'

    def get_form(self, request):
        return self.form_class(
            data=request.POST or None, files=None,
            background=self.character.background
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
        char_choices = get_model('characteradvancmentchoice')
        competence_choice = get_model('advancmentchoice').objects.get(code='CLASS_ROG_002')
        reason_obj = get_model('class').objects.get(name='Плут')

        char_choices.objects.get_or_create(
            character=character, choice=competence_choice,
            defaults={'reason': reason_obj}
        )


class POST_FEAT_003(POST_FEAT_001):
    """ Убийца """
    def apply(self, character):
        char_tools = get_model('charactertoolproficiency')
        for tool in get_model('tool').objects.filter(name__in=['Инструменты отравителя', 'Набор для грима']):
            _, _ = char_tools.objects.get_or_create(character=character, tool=tool)


class POST_FEAT_004:
    """ Комбинатор / Интриган """
    def apply(self, character):
        char_tools = get_model('charactertoolproficiency')
        for tool in get_model('tool').objects.filter(name__in=['Набор для фальсификации', 'Набор для грима']):
            _, _ = char_tools.objects.get_or_create(character=character, tool=tool)

        char_choices = get_model('characteradvancmentchoice')
        char_choices.objects.create(
            character=character,
            choice=get_model('advancmentchoice').objects.get(code='CLASS_ROG_003'),
            reason=get_model('subclass').objects.get(name='Комбинатор')
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
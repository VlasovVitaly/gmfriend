from django.apps import apps

from .forms import (
    AddCharLanguageFromBackground, AddCharSkillProficiency, CharacterBackgroundForm,
    ManeuversSelectForm, ManeuversUpgradeForm, MasterMindIntrigueSelect, SelectAbilityAdvanceForm,
    RogueCompetenceForm, CompetenceForm, SelectFeatureForm, SelectSubclassForm, SelectToolProficiency, KnownSpellsForm, ReplaceKnownSpellsForm, AddKnownSpellsForm
)

dnd5e_app = apps.app_configs['dnd5e']
get_model = dnd5e_app.get_model


class CharacterChoice:
    form_class = None
    queryset = None
    selection_limit = None
    pass_char = False  # Pass character to form_class

    def __init__(self, character, **kwargs):
        self.character = character
        self.extra = kwargs

    def get_form(self, request):
        if self.form_class is None:
            raise AssertionError('Choice formclass is not set')

        form_args = {'data': request.POST or None, 'files': None}

        if self.queryset:
            form_args['queryset'] = self.queryset

        if self.selection_limit:
            form_args['limit'] = self.selection_limit

        if self.pass_char:
            form_args['character'] = self.character

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


class CHAR_CLASS_SUBTYPE(CharacterChoice):
    """ ABS для выбора архетипа """
    form_class = SelectSubclassForm
    queryset = None
    level = None
    class_name = None

    def __init__(self, *args, **kwargs):
        if self.level is None:
            raise AssertionError

        if self.class_name is None:
            raise AssertionError

        self.queryset = get_model('subclass').objects.filter(parent__orig_name=self.class_name)
        super().__init__(*args, **kwargs)

    def apply_data(self, data):
        char_class = self.character.classes.get(klass__orig_name=self.class_name)
        char_class.subclass = data['subclass']
        char_class.save(update_fields=['subclass'])
        char_class._apply_subclass_advantages(self.level)


class CLASS_WAR_002(CHAR_CLASS_SUBTYPE):
    """ Воинский архетип """
    level = 3
    class_name = 'Fighter'


class CLASS_ROG_001(CHAR_CLASS_SUBTYPE):
    """ Архетип плута """
    level = 3
    class_name = 'Rogue'


class CLASS_BARD_001(CHAR_CLASS_SUBTYPE):
    """ Коллерия Бардов """
    level = 3
    class_name = 'Bard'


class CLASS_COMPETENCE(CharacterChoice):
    """ Компетентность """
    template = 'dnd5e/adventures/include/choices/competence.html'
    form_class = CompetenceForm
    selection_limit = 2

    def get_form(self, request):
        self.queryset = self.character.skills.filter(competence=False, proficiency=True)

        return super().get_form(request)

    def apply_data(self, data):
        data['skills'].update(competence=True)


class CLASS_ROG_002(CLASS_COMPETENCE):
    """ Компетентность Плут """
    form_class = RogueCompetenceForm
    pass_char = True

    def apply_data(self, data):
        super().apply_data(data)

        if data['tool']:
            data['tool'].competence = True
            data['tool'].save(update_fields=['competence'])


class CombatSuperiorityChoice(CharacterChoice):
    def improve_dice(self, new_value):
        superiority_dice = get_model('characterdice').objects.get(character=self.character, dtype='superiority')
        superiority_dice.dice = new_value
        superiority_dice.save(update_fields=['dice'])

    def add_dice(self):
        get_model('characterdice').objects.get(character=self.character, dtype='superiority').increase_count()

    def add_maneuvers(self, data):
        to_append = list(data['append'])
        if data.get('replace_src'):
            self.character.known_maneuvers.remove(data['replace_src'])
            to_append.append(data['replace_dst'])

        self.character.known_maneuvers.add(*to_append)

    def set_maneuvers(self, data):
        get_model('characterdice').objects.create(
            character=self.character, dtype='superiority', dice='1d8', count=4, maximum=4
        )
        self.character.known_maneuvers.set(data['maneuvers'])


class CLASS_BATTLE_001(CombatSuperiorityChoice):
    """ Мастер боевых исскуств / Боевое превосходство """
    form_class = ManeuversSelectForm
    selection_limit = 3

    def apply_data(self, data):
        self.set_maneuvers(data)


class CLASS_BATTLE_002(CombatSuperiorityChoice):
    """ Мастер боевых исскуств / Боевое превосходство (повышение)"""
    form_class = ManeuversUpgradeForm
    selection_limit = 2
    pass_char = True

    def apply_data(self, data):
        self.add_dice()
        self.add_maneuvers(data)


class CLASS_BATTLE_003(CombatSuperiorityChoice):
    """ Мастер боевых исскуств / Улучшенное боевое превосходство (кость и приемы) """
    form_class = ManeuversUpgradeForm
    selection_limit = 2
    pass_char = True

    def apply_data(self, data):
        # self.improve_dice('1d10')
        self.add_maneuvers(data)


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
    ''' Выбор мастерства классовых навыков на первом уровне'''
    form_class = AddCharSkillProficiency

    def get_form(self, request):
        return self.form_class(
            data=request.POST or None, files=None,
            limit=self.character.classes.first().klass.skill_proficiency_limit,
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

        return super().get_form(request)

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
        _ = get_model('characterbackground').objects.create(
            character=self.character, **data
        )


class CHAR_ADVANCE_005(CharacterChoice):
    ''' Выбор мастерства в одном классовом навыке'''
    form_class = AddCharSkillProficiency
    selection_limit = 1

    def get_form(self, request):
        return self.form_class(
            data=request.POST or None, files=None,
            limit=self.selection_limit,
            skills=self.character.skills.exclude(proficiency=True)
        )

    def apply_data(self, data):
        data['skills'].update(proficiency=True)


class CHAR_SPELLS_BARD(CharacterChoice):
    form_class = KnownSpellsForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        char_class = self.extra['choice'].reason
        self.queryset = get_model('spell').objects.filter(classes=char_class.klass_id)
        self.spellcasting = char_class.spellcasting[char_class.level]

    def get_form(self, request):
        form_args = {'data': request.POST or None, 'files': None}
        form_args['queryset'] = self.queryset
        form_args['spellcasting'] = self.spellcasting
        form_args['character'] = self.character

        return self.form_class(**form_args)

    def apply_data(self, data):
        self.character.known_spells.set(list(data['known_cantrips']) + list(data['known_spells']))


class CHAR_SPELLS_REPLACE(CharacterChoice):
    form_class = ReplaceKnownSpellsForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        char_class = self.extra['choice'].reason
        self.spellcasting = char_class.spellcasting

    def get_form(self, request):
        form_args = {'data': request.POST or None, 'files': None}
        form_args['spellcasting'] = self.spellcasting
        form_args['character'] = self.character

        return self.form_class(**form_args)

    def apply_data(self, data):
        self.character.known_spells.remove(*data['to_replace'])
        self.character.known_spells.add(*data['by_replace'])


class CHAR_SPELLS_APPEND(CharacterChoice):
    ''' Add new known spells after level up'''
    form_class = AddKnownSpellsForm

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        char_class = self.extra['choice'].reason
        spellcasting = char_class.current_spellcasting

        self.queryset = get_model('spell').objects.filter(classes=char_class.klass_id)
        self.queryset = self.queryset.filter(level__lte=len(spellcasting['slots'])).exclude(level=0)
        self.selection_limit = spellcasting['spells'] - self.character.known_spells.exclude(level=0).count()
        # TODO Check selection limit 0 or less

    def apply_data(self, data):
        self.character.known_spells.add(*data['spells'])


class CHAR_CANTRIPS_APPEND(CHAR_SPELLS_APPEND):
    ''' Add new known cantrips after level up'''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        char_class = self.extra['choice'].reason
        spellcasting = char_class.current_spellcasting

        self.queryset = get_model('spell').objects.filter(classes=char_class.klass_id).filter(level=0)
        self.selection_limit = spellcasting['cantrips'] - self.character.known_spells.filter(level=0).count()
        # TODO Check selection limit 0 or less


class POST_FEAT_001:
    def apply(self, character, **kwargs):
        wisdom = character.abilities.get(ability__orig_name='Wisdom')
        wisdom.saving_trow_proficiency = True
        wisdom.save(update_fields=['saving_trow_proficiency'])


class POST_FEAT_002:
    """ После получения умения компетенции Плута """
    def apply(self, character, **kwargs):
        char_choices = get_model('characteradvancmentchoice')
        competence_choice = get_model('advancmentchoice').objects.get(code='CLASS_ROG_002')

        char_choices.objects.get_or_create(character=character, choice=competence_choice)


class POST_FEAT_002_01:
    """ После получания умения компетенции Барда """
    def apply(self, character, **kwargs):
        get_model('characteradvancmentchoice').objects.get_or_create(
            character=character, choice=get_model('advancmentchoice').objects.get(code='CLASS_COMPETENCE')
        )


class POST_FEAT_003(POST_FEAT_001):
    """ Убийца """
    def apply(self, character, **kwargs):
        char_tools = get_model('charactertoolproficiency')
        for tool in get_model('tool').objects.filter(name__in=['Инструменты отравителя', 'Набор для грима']):
            _, _ = char_tools.objects.get_or_create(character=character, tool=tool)


class POST_FEAT_004:
    """ Комбинатор / Интриган """
    def apply(self, character, **kwargs):
        char_tools = get_model('charactertoolproficiency')
        for tool in get_model('tool').objects.filter(name__in=['Набор для фальсификации', 'Набор для грима']):
            _, _ = char_tools.objects.get_or_create(character=character, tool=tool)

        char_choices = get_model('characteradvancmentchoice')
        char_choices.objects.create(
            character=character,
            choice=get_model('advancmentchoice').objects.get(code='CLASS_ROG_003'),
        )


class POST_FEAT_005:
    """ Скаут / Выживальщик """
    def apply(self, character, **kwargs):
        character.skills.filter(skill__name__in=('Природа', 'Выживание')).update(proficiency=True)
        # NOTE mb need add extra_bonus to CharacterSkill


class POST_FEAT_006:
    """ Скаут / Превосходная мобильность """
    def apply(self, character, **kwargs):
        # TODO Add speeds to character model
        pass


class POST_WAR_STUDENT_001:
    """ Воин / Ученик войны """
    def apply(self, character, **kwargs):
        # TODO Нужен выбор, где учитываются изученные инструмены персонажа, PROF_TOOLS_003 не умеет
        char_choices = get_model('characteradvancmentchoice')
        char_choices.objects.create(
            character=character,
            choice=get_model('advancmentchoice').objects.get(code='PROF_TOOLS_003'),
        )


class POST_COMBAT_SUPERIORITY_001:
    """ Боевое превосходство """
    def apply(self, character, **kwargs):
        get_model('characterdice').objects.create(
            character=character, dtype='superiority', dice='1d8', count=4, maximum=4
        )
        char_choices = get_model('characteradvancmentchoice')
        char_choices.objects.create(
            character=character,
            choice=get_model('advancmentchoice').objects.get(code='CLASS_BATTLE_001'),
        )


class POST_COMBAT_SUPERIORITY_002:
    """ Улучшенное боевое превосходство """
    def apply(self, character, **kwargs):
        get_model('characterdice').objects.filter(character=character, dtype='superiority').update(dice='1d10')


class POST_COMBAT_SUPERIORITY_003:
    """ Улучшенное боевое превосходство+ """
    def apply(self, character, **kwargs):
        get_model('characterdice').objects.filter(character=character, dtype='superiority').update(dice='1d12')
        get_model('characterfeature').objects.filter(
            character=character, feature__post_action='POST_COMBAT_SUPERIORITY_002'
        ).delete()


class POST_SPELLCASTING_001:
    """ Использование заклинаний """
    def apply(self, character, **kwargs):
        # Find character class for this class
        char_class = character.classes.get(klass_id=kwargs['reason'].id)
        char_class.update_spellslots(char_class.level)

        char_choices = get_model('characteradvancmentchoice')
        char_choices.objects.create(
            character=character,
            choice=get_model('advancmentchoice').objects.get(code='CHAR_SPELLS_BARD'),
            reason=char_class
        )


class Choices:
    choices = {}

    def add(self, choice):
        name = choice.__name__
        if name not in self.choices:
            self.choices[name] = choice

    def get(self, name, char, **kwargs):
        return self.choices[name](char, **kwargs)

    def __getitem__(self, name):
        return self.choices[name]()


ALL_CHOICES = Choices()

ALL_CHOICES.add(CHAR_ADVANCE_001)
ALL_CHOICES.add(CHAR_ADVANCE_002)
ALL_CHOICES.add(CHAR_ADVANCE_003)
ALL_CHOICES.add(CHAR_ADVANCE_004)
ALL_CHOICES.add(CHAR_ADVANCE_005)
ALL_CHOICES.add(CHAR_SPELLS_BARD)
ALL_CHOICES.add(CHAR_SPELLS_REPLACE)
ALL_CHOICES.add(CHAR_SPELLS_APPEND)
ALL_CHOICES.add(CHAR_CANTRIPS_APPEND)
ALL_CHOICES.add(CLASS_BARD_001)
ALL_CHOICES.add(CLASS_COMPETENCE)
ALL_CHOICES.add(CLASS_BATTLE_001)
ALL_CHOICES.add(CLASS_BATTLE_002)
ALL_CHOICES.add(CLASS_BATTLE_003)
ALL_CHOICES.add(CLASS_ROG_001)
ALL_CHOICES.add(CLASS_ROG_002)
ALL_CHOICES.add(CLASS_ROG_003)
ALL_CHOICES.add(CLASS_WAR_001)
ALL_CHOICES.add(CLASS_WAR_002)
ALL_CHOICES.add(POST_COMBAT_SUPERIORITY_001)
ALL_CHOICES.add(POST_COMBAT_SUPERIORITY_002)
ALL_CHOICES.add(POST_COMBAT_SUPERIORITY_003)
ALL_CHOICES.add(POST_FEAT_001)
ALL_CHOICES.add(POST_FEAT_002)
ALL_CHOICES.add(POST_FEAT_002_01)
ALL_CHOICES.add(POST_FEAT_003)
ALL_CHOICES.add(POST_FEAT_004)
ALL_CHOICES.add(POST_FEAT_005)
ALL_CHOICES.add(POST_FEAT_006)
ALL_CHOICES.add(POST_SPELLCASTING_001)
ALL_CHOICES.add(PROF_TOOLS_001)
ALL_CHOICES.add(PROF_TOOLS_002)
ALL_CHOICES.add(PROF_TOOLS_003)
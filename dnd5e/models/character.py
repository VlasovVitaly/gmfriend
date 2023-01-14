from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from gm2m import GM2MField

from dnd5e import dnd
from dnd5e.model_fields import DiceField
from dnd5e.models.adventure import Adventure, Party
from dnd5e.models.base import (
    Ability, AdvancmentChoice, ArmorCategory, Background, BackgroundPath, Bond, Class,
    ClassArmorProficiency, ClassLevels, Feature, Flaw, Ideal, Maneuver, MultiClassProficiency,
    PersonalityTrait, Race, Skill, Spell, Subclass, Subrace, Tool, Weapon, WeaponCategory
)
from dnd5e.models.choices import ALIGNMENT_CHOICES, GENDER_CHOICES


class Character(models.Model):
    adventure = models.ForeignKey(
        Adventure, on_delete=models.CASCADE, editable=False,
        related_name='characters', related_query_name='character'
    )
    party = models.ForeignKey(
        Party, on_delete=models.SET_NULL, null=True, default=None, verbose_name='Отряд',
        related_name='members', related_query_name='member', blank=True,
    )
    name = models.CharField(verbose_name='Имя игрока', max_length=64, db_index=True)
    age = models.PositiveSmallIntegerField(verbose_name='Возраст')
    gender = models.PositiveSmallIntegerField(verbose_name='Пол', choices=GENDER_CHOICES)
    alignment = models.PositiveSmallIntegerField(
        null=True, choices=ALIGNMENT_CHOICES, default=10, verbose_name='Мировозрение'
    )
    race = models.ForeignKey(
        Race, on_delete=models.CASCADE, related_name='+', verbose_name='Раса',
    )
    subrace = models.ForeignKey(
        Subrace, on_delete=models.CASCADE, related_name='+', verbose_name='Разновидность расы', blank=True, null=True
    )
    level = models.PositiveSmallIntegerField(default=1, verbose_name='Уровень')
    proficiency = models.PositiveSmallIntegerField(verbose_name='Мастерство', default=2)
    background = models.ForeignKey(
        Background, on_delete=models.CASCADE, related_name='+', verbose_name='Предыстория'
    )
    dead = models.BooleanField(verbose_name='Мертв', default=False, editable=False)
    languages = models.ManyToManyField('Language', related_name='+', verbose_name='Владение языками', editable=False)
    armor_proficiency = models.ManyToManyField(
        ArmorCategory, related_name='+', verbose_name='Владение доспехами', blank=True
    )
    weapon_proficiency = GM2MField(WeaponCategory, Weapon, verbose_name='Владение оружием')
    known_maneuvers = models.ManyToManyField(Maneuver, related_name='+', verbose_name='Известные приёмы', editable=False)
    spellcasting_rules = models.CharField(max_length=512, null=True, default=None, editable=False)
    known_spells = models.ManyToManyField(verbose_name='Известные заклинания', to=Spell, related_name='+')

    class Meta:
        ordering = ['name', 'level']
        default_permissions = ()
        verbose_name = 'Персонаж'
        verbose_name_plural = 'Персонажи'

    def get_spellcasting_rules(self):
        raise NotImplementedError

    def init(self, klass):
        class_saving_trows = klass.saving_trows.all()
        abilities = []

        # Initial abilities values
        for ability in Ability.objects.all():
            to_add = CharacterAbilities(character=self, ability=ability)
            if ability in class_saving_trows:
                to_add.saving_trow_proficiency = True
            abilities.append(to_add)
        CharacterAbilities.objects.bulk_create(abilities)

        # Init Skills
        CharacterSkill.objects.bulk_create(
            CharacterSkill(character=self, skill=skill) for skill in Skill.objects.all()
        )

        # Backgroung skill proficiency
        self.skills.filter(skill__in=self.background.skills_proficiency.all()).update(proficiency=True)

        # Init Race Languages
        self.languages.set(self.race.languages.all())

        # Race|Subrace and Background Features
        features = self.race.features.order_by().union(self.background.features.order_by())
        features = features.union(self.subrace.features.order_by()) if self.subrace else features
        for feat in features:
            CharacterFeature.objects.create(character=self, feature=feat)

        for advantage in klass.level_feats.get(level=1).advantages.all():
            advantage.apply_for_character(self)

        # Tools proficiency
        tools = self.background.tools_proficiency.order_by()
        tools = tools.union(klass.tools_proficiency.order_by())
        CharacterToolProficiency.objects.bulk_create(
            [CharacterToolProficiency(character=self, tool=tool) for tool in tools]
        )

        # Armor proficiency
        self.armor_proficiency.set(klass.armor_proficiency.all())

        # Weapon proficiency
        self.weapon_proficiency.set(klass.weapon_proficiency.all())

        # Character choices
        char_choices = []

        # Background choices
        for choice in self.background.choices.all():
            char_choices.append(CharacterAdvancmentChoice(character=self, choice=choice))

        # Add background languages if need
        if self.background.known_languages:
            char_choices.append(
                CharacterAdvancmentChoice(
                    character=self, choice=AdvancmentChoice.objects.get(code='CHAR_ADVANCE_003')
                )
            )

        # Skills proficiency choice
        char_choices.append(
            CharacterAdvancmentChoice(
                character=self, choice=AdvancmentChoice.objects.get(code='CHAR_ADVANCE_002')
            )
        )

        # Background story
        char_choices.append(
            CharacterAdvancmentChoice(
                character=self, choice=AdvancmentChoice.objects.get(code='CHAR_ADVANCE_004')
            )
        )

        CharacterAdvancmentChoice.objects.bulk_create(char_choices)

        # Create dices
        CharacterDice.objects.create(character=self, dice=klass.hit_dice)

        self.spellcasting_rules = klass.codename
        self.save(update_fields=['spellcasting_rules'])  # FIXME seems dont need this field

    def init_new_multiclass(self, klass):  # TODO transaction???
        char_class = CharacterClass.objects.create(
            character=self,
            klass=klass,
            level=0
        )
        char_class.level_up()

        # Armor
        for armor in ClassArmorProficiency.objects.filter(klass_id=klass.id, in_multiclass=True):
            self.armor_proficiency.add(armor.armor_category)

        # Weapon
        profs = MultiClassProficiency.objects.filter(klass_id=klass.id)
        for weapon in profs.filter(content_type__app_label='dnd5e', content_type__model__in=['weaponcategory', 'weapon']):
            self.weapon_proficiency.add(weapon.proficiency)

        # Choices
        for choice in profs.filter(content_type__app_label='dnd5e', content_type__model='advancmentchoice'):
            CharacterAdvancmentChoice.objects.create(character=self, choice=choice.proficiency)

    def get_all_abilities(self):
        return self.abilities.values(
            'value', name=models.functions.Lower(models.F('ability__orig_name'))
        )

    def level_up(self):
        self.level = models.F('level') + 1
        self.save(update_fields=['level'])

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return self.name


class CharacterClass(models.Model):
    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='classes', related_query_name='class'
    )
    klass = models.ForeignKey(
        Class, on_delete=models.CASCADE, verbose_name='Класс', related_name='+'
    )
    subclass = models.ForeignKey(
        Subclass, on_delete=models.CASCADE, verbose_name='Архетип', related_name='+', null=True, default=None
    )
    level = models.PositiveSmallIntegerField(verbose_name='Уровень', default=1)

    # NOTE let DB calc max_prepared_spells
    prepared_spells = models.ManyToManyField(verbose_name='Подготовленные заклинания', to=Spell, related_name='+')

    class Meta:
        ordering = ['character', '-level', 'klass__name']
        unique_together = ['character', 'klass']
        default_permissions = ()
        verbose_name = 'Класс персонажа'
        verbose_name_plural = 'Классы персонажа'

    def _apply_class_advantages(self, level):
        try:
            klass_advantage = self.klass.level_feats.get(level=level)
        except ClassLevels.DoesNotExist:
            return

        for advantage in klass_advantage.advantages.all():
            advantage.apply_for_character(self.character)

    def _apply_subclass_advantages(self, level):
        try:
            subclass_advantage = self.subclass.level_feats.get(level=level)
        except ClassLevels.DoesNotExist:
            return

        for advantage in subclass_advantage.advantages.all():
            advantage.apply_for_character(self.character)

    def _increase_hit_dice(self):
        self.character.dices.filter(dtype='hit').update(
            count=models.F('count') + 1, maximum=models.F('maximum') + 1
        )

    def update_spellslots(self, level):
        # Get spellcasting tables
        spellcasting = dnd.SPELLCASTING.get(self.subclass.codename) if self.subclass_id else None
        spellcasting = spellcasting or dnd.SPELLCASTING.get(self.klass.orig_name.lower())
        spellslots = spellcasting[level]['slots']

        aggregations = {}
        for level, _ in enumerate(spellslots, 1):
            aggregations[f'spellslot_{level}'] = models.Count('id', filter=models.Q(level=level))
        char_spellslots = CharacterSpellSlot.objects.filter(character_id=self.character_id).aggregate(**aggregations)

        to_create = []
        spellcasting = [(lvl, slots - char_spellslots[f'spellslot_{lvl}']) for lvl, slots in enumerate(spellslots, 1)]
        for lvl, count in spellcasting:
            to_create.extend([CharacterSpellSlot(character_id=self.character_id, level=lvl) for _ in range(count)])

        _ = CharacterSpellSlot.objects.bulk_create(to_create)

    def level_up(self):
        self._apply_class_advantages(self.level + 1)

        if self.subclass_id:
            self._apply_subclass_advantages(self.level + 1)

        self.update_spellslots(self.level + 1)
        self._increase_hit_dice()

        self.level = models.F('level') + 1
        self.save(update_fields=['level'])

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.subclass if self.subclass_id else self.klass} {self.level} уровень'


class CharacterBackground(models.Model):
    character = models.OneToOneField(
        Character, on_delete=models.CASCADE, related_name='background_detail'
    )
    path = models.ForeignKey(
        BackgroundPath, on_delete=models.CASCADE, verbose_name='Жизненый путь', null=True, default=None
    )
    trait = models.ForeignKey(PersonalityTrait, on_delete=models.CASCADE, verbose_name='Черта')
    ideal = models.ForeignKey(Ideal, on_delete=models.CASCADE, verbose_name='Идеал')
    bond = models.ForeignKey(Bond, on_delete=models.CASCADE, verbose_name='Привязанность')
    flaw = models.ForeignKey(Flaw, on_delete=models.CASCADE, verbose_name='Слабость')

    class Meta:
        default_permissions = ()

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'


class CharacterAbilitiesQueryset(models.QuerySet):
    def increase_value(self, value):
        self.update(value=models.F('value') + value)


class CharacterAbilities(models.Model):
    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='abilities', related_query_name='ability'
    )
    ability = models.ForeignKey('Ability', on_delete=models.CASCADE, related_name='+')
    value = models.PositiveSmallIntegerField(verbose_name='Значение', default=11)
    saving_trow_proficiency = models.BooleanField(
        verbose_name='Мастерство в спасброске', default=False, editable=False
    )

    objects = CharacterAbilitiesQueryset.as_manager()

    class Meta:
        default_permissions = ()
        verbose_name = 'Характеристика персонажа'
        verbose_name_plural = 'Характеристики персонажей'

    @property
    def mod(self):
        return dnd.dnd_mod(self.value)

    @property
    def saving_trow_mod(self):
        if self.saving_trow_proficiency:
            return self.mod + self.character.proficiency

        return self.mod

    def __str__(self):
        return f'{self.ability}'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'


class CharacterSkillQueryset(models.QuerySet):
    def annotate_mod(self):
        abilities_queryset = CharacterAbilities.objects.filter(
            character_id=models.OuterRef('character_id'), ability_id=models.OuterRef('skill__ability_id')
        )
        mod_expression = models.functions.Floor((models.F('raw_value') - 10) / 2.0)
        return self.annotate(
            raw_value=models.Subquery(abilities_queryset.values('value')[:1], output_field=models.SmallIntegerField()),
            mod=models.Case(
                models.When(proficiency=True, competence=True, then=mod_expression + models.F('character__proficiency') * 2),
                models.When(proficiency=True, then=mod_expression + models.F('character__proficiency')),
                default=mod_expression,
                output_field=models.SmallIntegerField()
            ),
        )


class CharacterSkillManager(models.Manager):
    def get_queryset(self):
        return CharacterSkillQueryset(self.model, using=self._db, hints=self._hints).select_related('skill')


class CharacterSkill(models.Model):
    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='skills', related_query_name='skill'
    )
    skill = models.ForeignKey('Skill', on_delete=models.PROTECT, related_name='+')
    proficiency = models.BooleanField(default=False)
    competence = models.BooleanField(default=False)

    objects = CharacterSkillManager()

    class Meta:
        default_permissions = ()
        verbose_name = 'Навык персонажа'
        verbose_name_plural = 'Навыки персонажа'

    def __str__(self):
        return f'{self.skill}'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'


class CharacterFeature(models.Model):
    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='features', related_query_name='feature'
    )
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='+')
    max_charges = models.PositiveSmallIntegerField(null=True, blank=True, default=None)
    used = models.PositiveSmallIntegerField(blank=True, default=0)

    class Meta:
        ordering = ['character', 'feature__content_type', 'feature__source_id', 'feature__name']
        default_permissions = ()
        verbose_name = 'Особенность персонажа'
        verbose_name_plural = 'Особенности персонажей'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.character}: {self.feature}'


class CharacterAdvancmentChoiceQueryset(models.QuerySet):
    def aggregate_blocking_choices(self):
        return self.aggregate(
            blocking_choices=models.Count('id', filter=models.Q(choice__important=True)),
            total_choices=models.Count('id'),
        )


class CharacterAdvancmentChoice(models.Model):
    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='choices', related_query_name='choice'
    )
    choice = models.ForeignKey(
        AdvancmentChoice, on_delete=models.CASCADE, related_name='+'
    )

    objects = CharacterAdvancmentChoiceQueryset.as_manager()

    class Meta:
        ordering = ['character', '-choice__important', 'choice__name']
        default_permissions = ()
        verbose_name = 'Выбор персонажа'
        verbose_name_plural = 'Выборы персонажа'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'Выбор персонажа #{self.character_id}'


class CharacterDice(models.Model):
    DTYPE_CHOICES = (
        ('hit', 'Кость здоровья'),
        ('superiority', 'Кость превосходства'),
    )

    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='dices', related_query_name='dice'
    )
    dtype = models.CharField(max_length=32, choices=DTYPE_CHOICES, default='hit')
    dice = DiceField()
    count = models.PositiveSmallIntegerField(default=1)
    maximum = models.PositiveSmallIntegerField(default=1)

    class Meta:
        default_permissions = ()

    def increase_count(self, num=1):
        self.count = models.F('count') + num
        self.maximum = models.F('maximum') + num

        self.save(update_fields=['count', 'maximum'])

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.count}/{self.maximum} \u00d7 {self.dice}'


class CharacterToolProficiency(models.Model):
    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='tools_proficiency', related_query_name='tool'
    )
    tool = models.ForeignKey(Tool, on_delete=models.PROTECT, related_name='+')
    competence = models.BooleanField(default=False)

    class Meta:
        default_permissions = ()
        verbose_name = 'Инструменты персонажа'
        verbose_name_plural = 'Инструменты персонажа'

    def __str__(self):
        return f'{self.tool}'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'


class CharacterSpellSlot(models.Model):
    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name='spell_slots', related_query_name='spell_slot'
    )
    level = models.PositiveSmallIntegerField(verbose_name='Уровень')
    spent = models.BooleanField(verbose_name='Потрачен', default=False)

    class Meta:
        ordering = ['character_id', 'level', 'spent']
        default_permissions = ()
        verbose_name = 'Слот заклинания'
        verbose_name_plural = 'Слоты заклинаний'

    def __repr__(self):
        return f'[{self.__class__.__name__}]: {self.id}'

    def __str__(self):
        return f'{self.character} {self.level}'

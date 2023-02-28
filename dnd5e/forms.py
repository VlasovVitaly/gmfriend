from django import forms

from .models import (
    Character, CharacterAbilities, CharacterBackground, CharacterSkill,
    CharacterToolProficiency, Class, Feature, Language, Maneuver, Subclass, Tool, Spell
)
from .widgets import AbilityListBoxSelect


class CharacterForm(forms.ModelForm):
    klass = forms.ModelChoiceField(label='Класс', queryset=Class.objects.all())

    class Meta:
        model = Character
        fields = ['name', 'age', 'gender', 'alignment', 'race', 'subrace', 'background']

    field_order = ['name', 'age', 'gender', 'alignment', 'race', 'subrace', 'klass', 'background']

    def clean(self):
        race = self.cleaned_data['race']
        subrace = self.cleaned_data['subrace']

        if subrace and race != subrace.race:
            self.add_error('subrace', f'Разновидность «{subrace}» не подходит для расы «{race}»')

        if not subrace and race.has_subraces():
            self.add_error('subrace', f'У расы «{race}» есть разновидности')


class CharStatsForm(forms.ModelForm):
    class Meta:
        model = CharacterAbilities
        fields = ['value']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.character_id is not None:
            self.fields['value'].label = str(self.instance.ability)


CharacterStatsFormset = forms.modelformset_factory(CharacterAbilities, extra=0, form=CharStatsForm)


class CharacterBackgroundForm(forms.ModelForm):
    class Meta:
        model = CharacterBackground
        exclude = ['character']

    def __init__(self, *args, background, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.queryset = field.queryset.filter(background=background)
            field.label_from_instance = self.get_background_label

        if not self.fields['path'].queryset:
            del self.fields['path']
        else:
            self.fields['path'].required = True
            self.fields['path'].label = background.path_label

    @staticmethod
    def get_background_label(inst):
        return f'{inst.number}: {inst.text}'


class AddCharSkillProficiency(forms.Form):
    skills = forms.ModelMultipleChoiceField(queryset=CharacterSkill.objects.none())

    def __init__(self, *args, skills, limit, **kwargs):
        super().__init__(*args, **kwargs)

        self.limit = limit

        self.fields['skills'].queryset = skills
        self.fields['skills'].widget.attrs = {'class': 'selectpicker', 'data-max-options': self.limit}

    def clean_skills(self):
        skills = self.cleaned_data['skills']

        if skills.count() != self.limit:
            raise forms.ValidationError(f'Можно выбрать только {self.limit} навыка')

        return skills


class AddCharLanguageFromBackground(forms.Form):
    langs = forms.ModelMultipleChoiceField(queryset=Language.objects.none())

    def __init__(self, *args, queryset, limit, **kwargs):
        super().__init__(*args, **kwargs)

        self.langs_limit = limit

        self.fields['langs'].queryset = queryset
        self.fields['langs'].widget.attrs = {'class': 'selectpicker', 'data-max-options': limit}

    def clean_langs(self):
        langs = self.cleaned_data['langs']

        if langs.count() != self.langs_limit:
            raise forms.ValidationError(f'Можно выбрать только {self.langs_limit} языка')

        return langs


class SelectToolProficiency(forms.Form):
    tools = forms.ModelMultipleChoiceField(queryset=Tool.objects.none())

    def __init__(self, *args, queryset, limit, **kwargs):
        super().__init__(*args, **kwargs)

        self.limit = limit

        self.fields['tools'].queryset = queryset
        self.fields['tools'].widget.attrs = {'class': 'selectpicker', 'data-max-options': limit}

    def clean_tools(self):
        tools = self.cleaned_data['tools']

        if tools.count() > self.limit:
            raise forms.ValidationError(f'Можно выбрать только {self.limit} инструмент(ов)')

        return tools


class SelectFeatureForm(forms.Form):
    feature = forms.ModelChoiceField(queryset=Feature.objects.none())

    def __init__(self, *args, queryset, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['feature'].queryset = queryset
        self.fields['feature'].widget.attrs = {'class': 'selectpicker'}


class SelectSubclassForm(forms.Form):
    subclass = forms.ModelChoiceField(queryset=Subclass.objects.none())

    def __init__(self, *args, queryset, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['subclass'].queryset = queryset
        self.fields['subclass'].widget.attrs = {'class': 'selectpicker'}


class SelectAbilityAdvanceForm(forms.Form):
    abilities = forms.ModelMultipleChoiceField(queryset=CharacterAbilities.objects.none(), widget=AbilityListBoxSelect)

    def __init__(self, *args, queryset, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['abilities'].queryset = queryset


class CompetenceForm(forms.Form):
    skills = forms.ModelMultipleChoiceField(queryset=CharacterSkill.objects.none())

    class Media:
        js = ('js/competence-select.js', )

    def __init__(self, *args, queryset, limit, **kwargs):
        super().__init__(*args, **kwargs)

        self.skills_limit = limit
        self.fields['skills'].queryset = queryset

    def clean_skills(self):
        skills = self.cleaned_data['skills']

        if skills.count() != self.skills_limit:
            raise forms.ValidationError(f'Нужно выбрать ровно {self.skills_limit} навыка')

        return skills


class RogueCompetenceForm(CompetenceForm):
    tool = forms.ModelChoiceField(queryset=CharacterToolProficiency.objects.none(), required=False, empty_label=None)

    def __init__(self, *args, character, queryset, limit, **kwargs):
        super().__init__(*args, queryset=queryset, limit=limit, **kwargs)

        self.fields['tool'].queryset = CharacterToolProficiency.objects.filter(
            character_id=character.id, tool__name='Воровские инструменты'
        )

    def clean_skills(self):
        skills = self.cleaned_data['skills']

        if skills.count() > self.skills_limit:
            raise forms.ValidationError(f'Можно выбрать только {self.skills_limit} навыка')

        return skills

    def clean(self):
        skills_count = self.cleaned_data['skills'].count()
        tool = self.cleaned_data['tool']

        if tool and skills_count != 1:
            raise forms.ValidationError('С воровскими инструментами можно выбрать только 1 навык')

        if skills_count == 1 and not tool:
            raise forms.ValidationError(f'Можно выбрать только {self.skills_limit} навыка')


class MasterMindIntrigueSelect(forms.Form):
    tool = forms.ModelChoiceField(queryset=Tool.objects.none())
    languages = forms.ModelMultipleChoiceField(queryset=Language.objects.all())

    def __init__(self, *args, character, **kwargs):
        super().__init__(*args, **kwargs)

        # self.character = character  # MB we don't need this

        self.fields['tool'].queryset = Tool.objects.filter(category=Tool.CAT_GAMBLE).exclude(
            id__in=character.tools_proficiency.values_list('tool_id')
        )
        self.fields['tool'].widget.attrs = {'class': 'selectpicker'}

        self.fields['languages'].widget.attrs = {'class': 'selectpicker'}
        self.fields['languages'].queryset = Language.objects.exclude(id__in=character.languages.values_list('id'))


class ManeuversSelectForm(forms.Form):
    maneuvers = forms.ModelMultipleChoiceField(queryset=Maneuver.objects.all())

    def __init__(self, *args, limit, **kwargs):
        super().__init__(*args, **kwargs)

        self.limit = limit
        self.fields['maneuvers'].widget.attrs = {'class': 'selectpicker', 'data-max-options': limit}

    def clean_maneuvers(self):
        if self.cleaned_data['maneuvers'].count() != self.limit:
            raise forms.ValidationError(f'Необходимо выбрать ровно {self.limit} приёма')

        return self.cleaned_data['maneuvers']


class ManeuversUpgradeForm(forms.Form):
    replace_src = forms.ModelChoiceField(required=False, queryset=Maneuver.objects.none())
    replace_dst = forms.ModelChoiceField(required=False, queryset=Maneuver.objects.none())
    append = forms.ModelMultipleChoiceField(queryset=Maneuver.objects.none())

    def __init__(self, *args, character, limit, **kwargs):
        super().__init__(*args, **kwargs)

        self.limit = limit
        self.character = character

        known_maneuvers = character.known_maneuvers.all()
        unknown_maneuvers = Maneuver.objects.exclude(id__in=known_maneuvers)

        self.fields['replace_src'].queryset = known_maneuvers
        self.fields['replace_src'].widget.attrs = {'class': 'selecticker'}

        self.fields['replace_dst'].queryset = unknown_maneuvers
        self.fields['replace_dst'].widget.attrs = {'class': 'selectpcker'}

        self.fields['append'].queryset = unknown_maneuvers
        self.fields['append'].widget.attrs = {'class': 'selectpicker', 'data-max-options': limit}

    def clean(self):
        src = self.cleaned_data.get('replace_src')
        dst = self.cleaned_data.get('replace_dst')
        append = self.cleaned_data['append']

        if src and dst is None:
            self.add_error(
                'replace_dst', forms.ValidationError('При замене навыка необходимо указать на что поменять')
            )
        if dst and src is None:
            self.add_error(
                'replace_src', forms.ValidationError('При замене навыка нужно указать какой навык поменять')
            )

        if dst and append.filter(id=dst.id).exists():
            self.add_error(
                'replace_dst', forms.ValidationError('Вы хотите поменять на навык, который уже выбрали')
            )

    def clean_append(self):
        append = self.cleaned_data['append']
        if append.count() != self.limit:
            raise forms.ValidationError(f'Необходимо выбрать ровно {self.limit} приёма')

        return append


class ReplaceKnownSpellsForm(forms.Form):
    to_replace = forms.ModelMultipleChoiceField(queryset=Spell.objects.none())
    by_replace = forms.ModelMultipleChoiceField(queryset=Spell.objects.none())

    def __init__(self, *args, character, spellcasting, **kwargs):
        super().__init__(*args, **kwargs)

        current = character.known_spells.exclude(level=0)

        self.max_replaces = spellcasting['replace']['count']

        self.fields['to_replace'].queryset = current
        # TODO FOR CHARACTER
        self.fields['by_replace'].queryset = Spell.objects.exclude(level=0).exclude(id__in=current)

    def clean_to_replace(self):
        if self.cleaned_data['to_replace'].count() != self.max_replaces:
            raise forms.ValidationError(f'Необходимо выбрать ровно {self.max_replaces} заклинаний')

        return self.cleaned_data['to_replace']

    def clean_by_replace(self):
        if self.cleaned_data['by_replace'].count() != self.max_replaces:
            raise forms.ValidationError(f'Необходимо выбрать ровно {self.max_replaces} заклинаний')

        return self.cleaned_data['by_replace']


class KnownSpellsForm(forms.Form):
    known_cantrips = forms.ModelMultipleChoiceField(queryset=Spell.objects.none())
    known_spells = forms.ModelMultipleChoiceField(queryset=Spell.objects.none())

    def __init__(self, *args, character, spellcasting, queryset, **kwargs):
        super().__init__(*args, **kwargs)
        self.character = character

        self.max_cantrips = spellcasting['cantrips']
        self.max_spells = spellcasting['spells']

        self.fields['known_cantrips'].queryset = queryset.filter(level=0)
        self.fields['known_spells'].queryset = queryset.filter(level__gt=0, level__lte=len(spellcasting['slots']))

    def clean_known_cantrips(self):
        known = self.cleaned_data['known_cantrips']
        if known.count() != self.max_cantrips:
            raise forms.ValidationError(f'Необходимо выбрать ровно {self.max_cantrips} заговора')

        return known

    def clean_known_spells(self):
        known = self.cleaned_data['known_spells']
        if known.count() != self.max_spells:
            raise forms.ValidationError(f'Необходимо выбрать ровно {self.max_spells} заклинания')

        return known

    def clean(self):
        print(self.cleaned_data)
        self.cleaned_data['spells'] = self.cleaned_data['known_cantrips'].order_by().union(
            self.cleaned_data['known_spells'].order_by()
        )


class AddKnownSpellsForm(forms.Form):
    spells = forms.ModelMultipleChoiceField(queryset=Spell.objects.none())

    def __init__(self, *args, queryset, limit, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['spells'].queryset = queryset
        self.limit = limit

    def clean_spells(self):
        spells = self.cleaned_data['spells']
        if spells.count() != self.limit:
            raise forms.ValidationError(f'Необходимо выбрать ровно {self.limit} заклинаний')

        return spells
from django import forms

from .models import (
    Character, CharacterAbilities, CharacterBackground, CharacterSkill,
    CharacterToolProficiency, Feature, Language, Maneuver, Subclass, Tool
)
from .widgets import AbilityListBoxSelect


class CharacterForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = ['name', 'age', 'gender', 'alignment', 'race', 'klass', 'race', 'subrace', 'level', 'background']

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


class SelectCompetenceForm(forms.Form):
    skills_limit = 2
    skills = forms.ModelMultipleChoiceField(queryset=CharacterSkill.objects.none())
    tool = forms.ModelChoiceField(
        queryset=CharacterToolProficiency.objects.filter(tool__name='Воровские инструменты'), required=False, empty_label=None
    )

    def __init__(self, *args, queryset, **kwargs):
        # TODO Filter by character
        super().__init__(*args, **kwargs)

        self.fields['skills'].queryset = queryset

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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['maneuvers'].widget.attrs = {'class': 'selectpicker'}
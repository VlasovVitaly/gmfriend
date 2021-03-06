from django import forms

from .models import Character, CharacterAbilities, CharacterBackground, Skill, Language


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
    skills = forms.ModelMultipleChoiceField(queryset=Skill.objects.none())

    def __init__(self, *args, skills, klass_skills_limit, **kwargs):
        super().__init__(*args, **kwargs)

        self.skills_limit = klass_skills_limit

        self.fields['skills'].queryset = skills
        self.fields['skills'].widget.attrs = {'class': 'selectpicker', 'data-max-options': self.skills_limit}

    def clean_skills(self):
        skills = self.cleaned_data['skills']

        if skills.count() > self.skills_limit:
            raise forms.ValidationError(f'Можно выбрать только {self.skills_limit} навыка')

        return skills


class AddCharLanguageFromBackground(forms.Form):
    langs = forms.ModelMultipleChoiceField(queryset=Language.objects.none())

    def __init__(self, *args, languages, limit, **kwargs):
        super().__init__(*args, **kwargs)

        self.langs_limit = limit

        self.fields['langs'].queryset = languages
        self.fields['langs'].widget.attrs = {'class': 'selectpicker', 'data-max-options': limit}

    def clean_langs(self):
        langs = self.cleaned_data['langs']

        if langs.count() > self.langs_limit:
            raise forms.ValidationError(f'Можно выбрать только {self.langs_limit} языка')

        return langs
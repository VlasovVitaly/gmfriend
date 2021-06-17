from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render, reverse

from .choices import ALL_CHOICES
from .filters import MonsterFilter, SpellFilter
from .forms import (
    AddCharLanguageFromBackground, AddCharSkillProficiency,
    CharacterBackgroundForm, CharacterForm, CharacterStatsFormset
)
from .models import (
    NPC, Adventure, AdventureMonster, Character, CharacterAbilities, Language, Monster, Place, Spell, Stage, Zone
)


def index(request):
    context = {}
    if request.user.is_authenticated:
        context['adventures'] = Adventure.objects.filter(master=request.user)

    return render(request, 'dnd5e/index.html', context)


@login_required
def list_adventures(request):
    adventures = Adventure.objects.filter(master=request.user)

    context = {'adventures': adventures}

    return render(request, 'dnd5e/adventures/list.html', context)


@login_required
def adventure_detail(request, adv_id):
    adventure_qs = Adventure.objects.prefetch_related('monsters', 'stages')
    adventure = get_object_or_404(adventure_qs, id=adv_id)

    context = {
        'adventure': adventure, 'characters': adventure.characters.all()
    }

    return render(request, 'dnd5e/adventures/detail.html', context)


@login_required
def character_detail(request, adv_id, char_id):
    char = get_object_or_404(Character, id=char_id)
    adventure = get_object_or_404(Adventure, id=adv_id)
    choices = char.choices.filter(selected=False)

    context = {'char': char, 'adventure': adventure, 'choices': choices}

    return render(request, 'dnd5e/adventures/char/detail.html', context)


@login_required
def create_character(request, adv_id):
    adventure = get_object_or_404(Adventure, id=adv_id)
    form = CharacterForm(request.POST or None)

    if form.is_valid():
        char = form.save(commit=False)
        char.adventure = adventure

        with transaction.atomic():
            char.save()
            char.init()

        return redirect('dnd5e:adventure:character:detail', adv_id=adventure.id, char_id=char.id)

    context = {
        'adventure': adventure, 'form': form
    }

    return render(request, 'dnd5e/adventures/char/create.html', context)


@login_required
def set_character_stats(request, adv_id, char_id):
    char = get_object_or_404(Character, id=char_id)
    adventure = get_object_or_404(Adventure, id=adv_id)

    charstats_formset = CharacterStatsFormset(
        data=request.POST or None,
        files=request.FILES or None,
        queryset=CharacterAbilities.objects.filter(character=char),
    )
    if charstats_formset.is_valid():
        charstats_formset.save()

        return redirect('dnd5e:adventure:character:detail', adv_id=adventure.id, char_id=char.id)

    context = {'char': char, 'adventure': adventure, 'formset': charstats_formset}

    return render(request, 'dnd5e/adventures/char/set_stats.html', context)


@login_required
def set_character_background(request, adv_id, char_id):
    char = get_object_or_404(Character, id=char_id)
    adventure = get_object_or_404(Adventure, id=adv_id)

    form = CharacterBackgroundForm(request.POST or None, background=char.background)

    if hasattr(char, 'background_detail'):
        form = CharacterBackgroundForm(
            request.POST or None, background=char.background, instance=char.background_detail
        )
    else:
        form = CharacterBackgroundForm(request.POST or None, background=char.background)

    if form.is_valid():
        background = form.save(commit=False)

        if background.character_id is None:
            background.character = char

        background.save()

    context = {'char': char, 'adventure': adventure, 'form': form}

    return render(request, 'dnd5e/adventures/char/set_background.html', context)


@login_required
def set_languages(request, adv_id, char_id):
    adventure = get_object_or_404(Adventure, id=adv_id)
    char = get_object_or_404(Character, id=char_id, adventure=adventure)

    max_languages = char.background.known_languages
    if not max_languages:
        raise Http404()

    possible_langs = Language.objects.exclude(id__in=char.race.languages.values('id'))
    form = AddCharLanguageFromBackground(
        data=request.POST or None, languages=possible_langs, limit=max_languages,
        initial={'langs': char.languages.exclude(id__in=char.race.languages.values('id'))}
    )

    if form.is_valid():
        with transaction.atomic():
            char.languages.set(
                char.race.languages.order_by().union(form.cleaned_data['langs'].order_by()), clear=True
            )

    context = {
        'char': char, 'adventure': adventure,
        'current': char.languages.all(),
        'max_languages': max_languages,
        'form': form,
    }

    return render(request, 'dnd5e/adventures/char/set_languages.html', context)


@login_required
def set_skills_proficiency(request, adv_id, char_id):
    char = get_object_or_404(Character, id=char_id)
    adventure = get_object_or_404(Adventure, id=adv_id)

    char_skills = char.skills.all().annotate_from_background(char.background)

    form = AddCharSkillProficiency(
        request.POST or None,
        skills=char_skills.exclude(from_background=True),
        klass_skills_limit=char.klass.skill_proficiency_limit,
        initial={'skills': char_skills.exclude(from_background=True).filter(proficiency=True)}
    )

    if form.is_valid():
        with transaction.atomic():
            char_skills.exclude(from_background=True).update(proficiency=False)
            form.cleaned_data['skills'].update(proficiency=True)

    context = {
        'char': char, 'adventure': adventure, 'form': form, 'current': char_skills.filter(proficiency=True)
    }

    return render(request, 'dnd5e/adventures/char/set_skills.html', context)


@login_required
@transaction.atomic()
def resolve_char_choices(request, adv_id, char_id):
    adventure = get_object_or_404(Adventure, id=adv_id)
    char = get_object_or_404(Character, id=char_id, adventure=adventure)

    choice = char.choices.filter(selected=False).first()

    selector = ALL_CHOICES[choice.choice.code](char)
    form = selector.get_form(request, char)

    if form.is_valid():
        selector.apply_data(form.cleaned_data)
        if choice.choice.oneshoot:
            choice.delete()
        else:
            choice.selected = True
            choice.save(update_fields=['selected'])

        return redirect(reverse('dnd5e:adventure:character:detail', kwargs={'adv_id': adventure.id, 'char_id': char.id}))

    context = {
        'adventure': adventure, 'char': char, 'choice': choice, 'form': form,
        'template': getattr(selector, 'template', None)
    }

    return render(request, 'dnd5e/adventures/char/resolve_choices.html', context)


@login_required
def stage_detail(request, stage_id):
    stage = get_object_or_404(Stage.objects.prefetch_detail().annotate_detail(), id=stage_id)

    context = {'stage': stage, 'adventure': stage.adventure}

    return render(request, 'dnd5e/adventures/stage_detail.html', context)


@login_required
def place_detail(request, place_id):
    place = get_object_or_404(Place, id=place_id)
    stage = get_object_or_404(Stage.objects.prefetch_detail().annotate_detail(), id=place.stage_id)

    context = {
        'place': place, 'stage': stage, 'adventure': place.stage.adventure,
        'place_ct': ContentType.objects.get_for_model(Place),
        'zone_ct': ContentType.objects.get_for_model(Zone),
    }
    return render(request, 'dnd5e/adventures/place_detail.html', context)


@login_required
def npc_detail(request, npc_id):
    npc = get_object_or_404(NPC, id=npc_id)

    context = {
        'npc': npc
    }

    return render(request, 'dnd5e/adventures/npc_detail.html', context)


@login_required
def monsters_interaction(request, location_ct, location_id):
    monsters = AdventureMonster.objects.filter(
        location_ct_id=location_ct, location_id=location_id
    )
    location = ContentType.objects.get_for_id(location_ct).get_object_for_this_type(id=location_id)

    context = {'monsters': monsters, 'location': location}

    return render(request, 'dnd5e/adventures/monsters_interaction.html', context)


def spells_list(request):
    spells = Spell.objects.all().prefetch_related('classes').select_related('school')

    context = {'sfilter': SpellFilter(request.GET, queryset=spells)}

    return render(request, 'dnd5e/spells_list.html', context)


def monsters_list(request):
    monsters = Monster.objects.all()

    context = {'mfilter': MonsterFilter(request.GET, queryset=monsters)}

    return render(request, 'dnd5e/monsters_list.html', context)


def level_tables(request):
    bard_table = (
        (1, '+2', 'Использование заклинаний, Вдохновение барда (d6)', 2, 4, (2, '', '', '', '', '', '', '', '')),
        (2, '+2', 'Мастер на все руки, Песнь отдыха (d6)', 2, 5, (3, '', '', '', '', '', '', '', '')),
        (3, '+2', 'Коллегия бардов, Компетентность', 2, 6, (4, 2, '', '', '', '', '', '', '')),
        (4, '+2', 'Увеличение характеристик', 3, 7, (4, 3, '', '', '', '', '', '', '')),
        (5, '+3', 'Вдохновение барда (d8), Источник вдохновения', 3, 8, (4, 3, 2, '', '', '', '', '', '')),
        (6, '+3', 'Контрочарование, Умение коллегии бардов', 3, 9, (4, 3, 3, '', '', '', '', '', '')),
        (7, '+3', '', 3, 10, (4, 3, 3, 1, '', '', '', '', '')),
        (8, '+3', 'Увеличение характеристик', 3, 11, (4, 3, 3, 2, '', '', '', '', '')),
        (9, '+4', 'Песнь отдыха (d8)', 3, 12, (4, 3, 3, 3, 1, '', '', '', '')),
        (10, '+4', 'Вдохновение барда (d10), Компетентность, Тайны магии', 4, 14, (4, 3, 3, 3, 2, '', '', '', '')),
        (11, '+4', '', 4, 15, (4, 3, 3, 3, 2, 1, '', '', '')),
        (12, '+4', 'Увеличение характеристик', 4, 15, (4, 3, 3, 3, 2, 1, '', '', '')),
        (13, '+5', 'Песнь отдыха (d10)', 4, 16, (4, 3, 3, 3, 2, 1, 1, '', '')),
        (14, '+5', 'Тайны магии, Умение коллегии бардов', 4, 18, (4, 3, 3, 3, 2, 1, 1, '', '')),
        (15, '+5', 'Вдохновение барда (d12)', 4, 19, (4, 3, 3, 3, 2, 1, 1, 1, '')),
        (16, '+5', 'Увеличение характеристик', 4, 19, (4, 3, 3, 3, 2, 1, 1, 1, '')),
        (17, '+6', 'Песнь отдыха (d12)', 4, 20, (4, 3, 3, 3, 2, 1, 1, 1, 1)),
        (18, '+6', 'Тайны магии', 4, 22, (4, 3, 3, 3, 3, 1, 1, 1, 1)),
        (19, '+6', 'Увеличение характеристик', 4, 22, (4, 3, 3, 3, 3, 2, 1, 1, 1)),
        (20, '+6', 'Превосходное вдохновение', 4, 22, (4, 3, 3, 3, 3, 2, 2, 1, 1)),
    )

    context = {
        'bard': bard_table,
    }

    return render(request, 'dnd5e/level_tables.html', context)
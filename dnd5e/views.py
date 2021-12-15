from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render, reverse

from dnd5e import dnd

from .choices import ALL_CHOICES
from .filters import MonsterFilter, SpellFilter
from .forms import CharacterForm, CharacterStatsFormset
from .models import (
    NPC, Adventure, AdventureMonster, Character, CharacterAbilities, CharacterAdvancmentChoice,
    CharacterClass, Class, ClassLevels, Monster, Place, Spell, Stage, Subclass, Zone
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
    choices = char.choices.select_related('choice')

    context = {'char': char, 'adventure': adventure, 'choices': choices}
    context.update(choices.aggregate_blocking_choices())

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
            CharacterClass.objects.create(character=char, klass=form.cleaned_data['klass'])
            char.init(form.cleaned_data['klass'])

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
def level_up(request, adv_id, char_id, class_id=None):
    char = get_object_or_404(Character, id=char_id)
    adventure = get_object_or_404(Adventure, id=adv_id)

    if class_id is not None:
        with transaction.atomic():
            char.level_up()
            klass = CharacterClass.objects.get(id=class_id)
            klass.level_up()

        return redirect('dnd5e:adventure:character:detail', adventure.id, char.id)

    context = {'char': char, 'adventure': adventure, 'classes': char.classes.all()}

    return render(request, 'dnd5e/adventures/char/level_up.html', context)


@login_required
def level_up_multiclass(request, adv_id, char_id):

    char = get_object_or_404(Character, id=char_id)
    adventure = get_object_or_404(Adventure, id=adv_id)

    if request.method == 'POST' and request.POST.get('klass_id'):
        # TODO check that klass can be assigned
        char.init_new_multiclass(get_object_or_404(Class, id=request.POST['klass_id']))

        return redirect('dnd5e:adventure:character:detail', adv_id=adventure.id, char_id=char.id)

    possible_classes = Class.objects.all()
    taken_classes = char.classes.values_list('klass_id', flat=True)

    # Create character ability mapping
    char_abilities = char.get_all_abilities()
    char_abilities = dnd.CharacterAbilitiesLimit({abil['name']: abil['value'] for abil in char_abilities})

    for cls in possible_classes:
        if cls.id in taken_classes:
            cls.disabled_message = 'вы уже овладели этим классом'
            continue

        mar = dnd.MULTICLASS_RESTRICTONS[cls.orig_name.lower()]

        if not char_abilities.check(mar):
            cls.disabled_message = 'вы не можете овладеть этим классом по проверкам характеристик'

    context = {'char': char, 'adventure': adventure, 'classes': possible_classes}

    return render(request, 'dnd5e/adventures/char/level_up_multiclass.html', context)


@login_required
@transaction.atomic()
def resolve_char_choice(request, adv_id, char_id, choice_id):
    adventure = get_object_or_404(Adventure, id=adv_id)
    char = get_object_or_404(Character, id=char_id, adventure=adventure)
    choice = get_object_or_404(CharacterAdvancmentChoice.objects.select_related('choice'), id=choice_id)

    if not choice.choice.important and char.choices.filter(choice__important=True).exists():
        # Can't make choice if more important choice exists for this char
        messages.info(request, 'Для этого персонажа нужно сделать более важный выбор')
        return redirect(reverse('dnd5e:adventure:character:detail', kwargs={'adv_id': adventure.id, 'char_id': char.id}))

    selector = ALL_CHOICES[choice.choice.code](char)
    form = selector.get_form(request)
    print(request.POST)

    if form.is_valid():
        selector.apply_data(form.cleaned_data)
        choice.delete()

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
    monsters = Monster.objects.select_related('source', 'mtype').prefetch_related('senses', 'traits', 'skills', 'actions')

    context = {'mfilter': MonsterFilter(request.GET, queryset=monsters)}

    return render(request, 'dnd5e/monsters_list.html', context)


def level_tables(request):
    context = {'klasses': Class.objects.prefetch_related('subclass_set').all()}
    return render(request, 'dnd5e/level_tables.html', context)


def level_table_detail(request, subklass_id):
    subklass = get_object_or_404(Subclass.objects.select_related('parent'), id=subklass_id)

    context = {'subklass': subklass}
    context.update(**ClassLevels.tables.html_table(subklass))

    return render(request, 'dnd5e/level_table.html', context)
from django.contrib import admin

from markdownx.admin import MarkdownxModelAdmin

from . import models


class MonsterSkillsInline(admin.TabularInline):
    model = models.MonsterSkill
    extra = 0


class MonsterActionInline(admin.TabularInline):
    model = models.MonsterAction
    extra = 0


class MonsterSensesInline(admin.TabularInline):
    model = models.MonsterSense
    extra = 0


class MonsterTraitInline(admin.TabularInline):
    model = models.MonsterTrait
    extra = 0


class MonsterAdmin(admin.ModelAdmin):
    inlines = (MonsterSkillsInline, MonsterActionInline, MonsterSensesInline, MonsterTraitInline)


class CharacterAbilityInline(admin.TabularInline):
    model = models.CharacterAbilities
    extra = 0


class CharacterAdmin(admin.ModelAdmin):
    inlines = (CharacterAbilityInline, )


class ToolAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'cost')


admin.site.register(models.Adventure)
admin.site.register(models.Race)
admin.site.register(models.Class)
admin.site.register(models.RuleBook)
admin.site.register(models.SpellSchool)
admin.site.register(models.Spell)
admin.site.register(models.Character, CharacterAdmin)
admin.site.register(models.MonsterType)
admin.site.register(models.CombatAction)
admin.site.register(models.Ability)
admin.site.register(models.Language)
admin.site.register(models.Skill)
admin.site.register(models.Sense)
admin.site.register(models.Monster, MonsterAdmin)
admin.site.register(models.Stage, MarkdownxModelAdmin)
admin.site.register(models.NPC, MarkdownxModelAdmin)
admin.site.register(models.Subrace)
admin.site.register(models.Place, MarkdownxModelAdmin)
admin.site.register(models.Trap)
admin.site.register(models.Knowledge)
admin.site.register(models.Zone, MarkdownxModelAdmin)
admin.site.register(models.AdventureMap)
admin.site.register(models.Treasure)
admin.site.register(models.MoneyAmount)
admin.site.register(models.Stuff)
admin.site.register(models.AdventureMonster)
admin.site.register(models.Quest)
admin.site.register(models.Item)
admin.site.register(models.NPCRelation)
admin.site.register(models.Party)
admin.site.register(models.Background)
admin.site.register(models.PersonalityTrait)
admin.site.register(models.Ideal)
admin.site.register(models.Feature)
admin.site.register(models.Bond)
admin.site.register(models.Flaw)
admin.site.register(models.BackgroundPath)
admin.site.register(models.Tool, ToolAdmin)
admin.site.register(models.AdvancmentChoice)
admin.site.register(models.ClassLevels)
admin.site.register(models.ClassLevelAdvance)
admin.site.register(models.Subclass)
admin.site.register(models.Maneuver)
admin.site.register(models.ArmorCategory)
admin.site.register(models.WeaponCategory)
admin.site.register(models.Weapon)
admin.site.register(models.MultiClassProficiency)
admin.site.register(models.ClassArmorProficiency)
admin.site.register(models.CharacterSpellSlot)
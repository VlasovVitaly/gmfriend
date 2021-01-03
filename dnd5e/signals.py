from django.utils.text import slugify


def update_slug(sender, instance, **kwargs):
    if instance.orig_name:
        instance.slug = slugify(instance.orig_name)


def set_monster_hp(sender, instance, **kwargs):
    if instance.current_hp is None:
        instance.current_hp = instance.monster.hit_points
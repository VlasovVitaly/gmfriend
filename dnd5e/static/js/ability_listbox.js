"use strict";

function stat_mod (num) {
    let ret = Math.floor((num - 10) / 2);

    if (isNaN(ret)) { return '?'}

    return (ret > 0) ? "+" + ret : ret;
}

function recalculate_item(list_item, increase_value) {
    let newvalue = list_item.data('orig-value') + increase_value;

    list_item.children('.ability-val').text(newvalue);
    list_item.children('.ability-mod').text(stat_mod(newvalue));
}

function OnFormSubmit(event) {
    let form = jQuery(event.currentTarget);

    event.data.data('selected').forEach(function ( element ) {
        form.prepend(jQuery(`<input type="hidden" name="abilities" value="${element}" />`));
    });

    return true;
}

function ListBoxToggleActiveCallback(event) {
    let list_item = jQuery(this)
    let item_value = parseInt(list_item.data('value'), 10);
    let list_root = list_item.parent();
    let is_active = !list_item.hasClass('active');
    let selected_items = list_item.siblings('.active').length;
    let increase_value;

    event.preventDefault();

    if (is_active) {
        if (selected_items >= 2) { return /* selection limit */}
        list_root.data('selected').push(item_value);
        selected_items += 1;
    } else {
        list_root.data('selected').splice(list_root.data('selected').indexOf(item_value), 1);
    }

    list_item.toggleClass('active');

    switch (selected_items) {
        case 2:
            increase_value = 1;
            break;
        case 1:
            increase_value = 2;
            break;
        case 0:
            increase_value = 0;
            break;
        default:
            break;
    }

    recalculate_item(list_item, (is_active) ? increase_value : 0);

    list_item.parent().data('increase-bonus', increase_value);

    list_item.siblings('a.list-group-item-action.active').each(function (index) {
        recalculate_item(jQuery(this), increase_value);
    });
}

jQuery(function () {
    let root_item = jQuery('.abilities-listbox');
    root_item.data('increase-bonus', 0).data('selected', new Array());
    root_item.closest('form').submit(root_item, OnFormSubmit);

    let items = root_item.children('a.list-group-item-action');
    items.click(ListBoxToggleActiveCallback);
});
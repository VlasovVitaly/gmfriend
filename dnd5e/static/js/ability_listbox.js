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

function FormSubmitCallback(event) {
    event.preventDefault();

    let csrf_token = jQuery('[name=csrfmiddlewaretoken').val();

    jQuery.post({
        'url': window.location,
        'data': {'abilities': event.data.data('selected'), 'csrfmiddlewaretoken': csrf_token},
        'error': function (a, b, c) {console.log(a,b,c)},
        'traditional': true,
        'success': function (data, textStatus, jqXHR) { document.write(data) }
    })
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
        if (selected_items >= 2) { console.log("Reached selection limit"); return }
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
    ///// TODO make it more abstract and DRY
    let root_item = jQuery('#id_abilities');
    root_item.data('increase-bonus', 0).data('selected', new Array());
    jQuery('a.list-group-item-action').click(ListBoxToggleActiveCallback);
    jQuery('button.btn-submit').click(root_item, FormSubmitCallback);
});
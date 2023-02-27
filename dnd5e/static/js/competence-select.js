"use strict";

jQuery(function () {
    const max_selection_limit = 2;
    const root = jQuery('#competence-list-item');

    function init_list_item (list_item) {
        list_item.data('skills', new Set());
        list_item.data('tools', new Set());
    }

    function form_on_sunmit(event) {
        event.preventDefault();

        let form_data = {
            'skills': Array.from(event.data.data('skills')),
            'tool': Array.from(event.data.data('tools')),
            'csrfmiddlewaretoken': jQuery('[name=csrfmiddlewaretoken').val()
        };

        jQuery.post({
            'url': window.location,
            'data': form_data,
            'error': function (a, b, c) {console.log(a,b,c)},
            'traditional': true,
            'success': function (data, textStatus, jqXHR) { document.write(data) }
        })
        
    }
    function list_item_click (event) {
        event.preventDefault();

        const item = jQuery(this);
        const selected_items = item.siblings('.active').length;

        // Check selection limit
        if (selected_items >= max_selection_limit) { return }

        const value = parseInt(item.data('value'), 10);
        const data_set = event.data.data(item.data('field-type'));
        const set_selection = !item.hasClass('active');

        item.hasClass('active') ? data_set.delete(value) : data_set.add(value);
        jQuery(this).toggleClass('active');
    }

    init_list_item(root);
    jQuery('.list-group-item-action').click(root, list_item_click);
    jQuery('#competence-selection-form').submit(root, form_on_sunmit);

});
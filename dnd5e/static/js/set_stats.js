"use strict";
function stat_mod (num) {
    let ret = Math.floor((num - 10) / 2);

    if (isNaN(ret)) { return '?'}

    return (ret > 0) ? "+" + ret : ret;
}

jQuery(function () {
    jQuery('form#edit-stats-form .form-control').map(function (index, elt) {
        let jq_elt = jQuery(elt);
        let mod_label = jq_elt.parent().find('.mod-label');

        jq_elt.on('input', {label: mod_label}, function (event) {
            console.log(typeof(event.currentTarget.value));
            event.data.label.text(stat_mod(parseInt(event.currentTarget.value, 10)));
        });
        
        if (elt.value) {
            mod_label.text(stat_mod(parseInt(elt.value, 10)));
        }
    });
});
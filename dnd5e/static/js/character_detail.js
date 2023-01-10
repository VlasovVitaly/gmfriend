"use strict";

function on_detail_tab_click (event, content) {
    event.preventDefault();

    fetch(this.href)
    .then( resp => resp.text() )
    .then( html => content.innerHTML = html )
    .catch( err => console.log(err) )

    document.querySelectorAll('.character-detail-tab').forEach( elt => { elt.classList.remove('active') });
    this.classList.add('active');
}

(function () {
    const content = document.getElementById('character-data-content');

    if (!content) {
        console.error('Character data content element was not found');
        return;
    }

    document.querySelectorAll('.character-detail-tab').forEach(elt => {
        elt.addEventListener('click', function (event) {
            on_detail_tab_click.call(this, event, content);
        });
    });
})();
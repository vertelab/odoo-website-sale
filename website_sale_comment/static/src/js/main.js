$(document).ready(function () {
    $comment.find("[name='note']").change(function (ev) {
        var note = $(ev.currentTarget).val();
        openerp.jsonRpc("/shop/order/note", 'call', {
            'note': note,
        })
    });
});

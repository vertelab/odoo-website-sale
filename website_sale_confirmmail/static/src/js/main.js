$(document).ready(function () {
    $("#order_comment").find("[name='note']").on('change', function () {
        openerp.jsonRpc("/shop/order/note", 'call', {
            'note': $(this).val(),
        });
    });
});

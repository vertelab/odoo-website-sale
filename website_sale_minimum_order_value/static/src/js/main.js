$(document).ready(function () {
    $("#order_comment").find("[name='note']").on('change', function () {
        openerp.jsonRpc("/shop/order/note", 'call', {
            'note': $(this).val(),
        });
    });
});

$('.oe_website_sale').find(".oe_cart input.js_quantity").on("change", function () {
    $.ajax({
        url: '/shop/allowed_order/?order=' + $("a#process_checkout").data("order"),
        type: 'post',
        data: {},
        success: function(data) {
            if (data == '1') {
                $("a#process_checkout").attr("disabled", false);
            }
            if (data == '0') {
                $("a#process_checkout").attr("disabled", true);
            }
        }
    });
});

$(document).ready(function () {
    $("#order_comment").find("[name='note']").on('change', function () {
        openerp.jsonRpc("/shop/order/note", 'call', {
            'note': $(this).val(),
        });
    });
    console.log($("tr#order_total_untaxed").find("span.oe_currency_value").text());
    $('.oe_website_sale').each(function () {
        var oe_website_sale = this;
        $(oe_website_sale).on('click', 'a.js_add_cart_json', function (ev) {
        }).done(function() {
            $.ajax({
                url: '/shop/allowed_order',
                type: 'post',
                data: {'order_id': $("a#process_checkout").data("order")},
                success: function(data){
                    console.log(data);
                    //~ $("#top_menu").load(location.href + " #top_menu");
                }
            });
        });
    });
});

$(document).ready(function () {
    $('form[action="/shop/cart/update"] .a-submit, #comment .a-submit').off('click').on('click', function (e) {
        e.preventDefault();
        $.ajax({
            url: '/shop/cart/update',
            type: 'post',
            data: $(this).closest('form').serialize(),
            success: function(){
                $("#top_menu").load(location.href + " #top_menu");
            }
        });
    });
});

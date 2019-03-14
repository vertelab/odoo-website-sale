$(document).ready(function(){
    
    var website = openerp.website;
    website.add_template_file('/website_sale_stock/static/src/xml/website_sale_stock_product_availability.xml');
    
    $('.oe_website_sale').each(function () {
        var oe_website_sale = this;
        $(oe_website_sale).on('change', 'input.js_variant_change, select.js_variant_change, ul[data-attribute_value_ids]', function (ev) {
            var $ul = $(ev.target).closest('.js_add_cart_variants');
                check_stock($ul);
        });
    })
           
    function check_stock($ul) {        
            var $parent = $ul.closest('.js_product');
            var $product_id = $parent.find('input.product_id').first();
            var $price = $parent.find(".oe_price:first .oe_currency_value");
            var $default_price = $parent.find(".oe_default_price:first .oe_currency_value");
            var $optional_price = $parent.find(".oe_optional:first .oe_currency_value");
            var variant_ids = $ul.data("attribute_value_ids");
            var values = [];
                
            $parent.find('input.js_variant_change:checked, select.js_variant_change').each(function () {
                values.push(+$(this).val());
            });
            
            openerp.jsonRpc("/shop/get_stock_values", 'call', {
                'product_id': $product_id.val()})
            .then(function (res) {
                var $input_add_qty = $parent.find('input[name="add_qty"]');
                var qty_add = $input_add_qty.val();
                var qty_avail = res['qty_available'];
                var qty_cart = res['cart_qty'];
                var qty_left = qty_avail - qty_cart - qty_add;
                
                invent_avail = res['inventory_availability'];
                
                // Make add to cart button clickable in case it has been disabled before.
                $parent.find('#add_to_cart').removeClass('disabled out_of_stock');

                if (res.product_type === 'product' && (invent_avail == 'always' || invent_avail == 'threshold')) {
                    if (qty_left < 0) {
                    qty_left = 0
                    }
                    
                    // Handle case when manually write in input
                    if (qty_add > qty_avail - qty_cart) {
                        qty_add  = (qty_avail - qty_cart) || 1;
                        $input_add_qty.val(qty_add);
                    }
                    
                    if (qty_add > qty_avail || qty_avail < 1 || qty_add < 1) {
                        // Disable add to cart button.
                        $parent.find('#add_to_cart').addClass('disabled out_of_stock');
                    }
                }
            
                var QWeb = openerp.qweb;
                var $message = $(QWeb.render(
                    'product_availability',
                    res
                ));
                $('div.availability_messages').html($message);
            });
        };
        
        check_stock($('input.js_variant_change, select.js_variant_change, ul[data-attribute_value_ids]').first().closest('.js_add_cart_variants'));
});


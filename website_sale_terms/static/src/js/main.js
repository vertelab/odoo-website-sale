$(document).ready(function () {
    var $payment = $("#payment_method");
    $payment.find('button').attr('disabled','disabled');
    $("#terms_and_conditions").find("[name='terms_and_conditions']").on('change', function () {
        openerp.jsonRpc("/shop/order/terms_and_conditions", 'call', {
            'accepted': $(this).val(),
        });
    });
    $("#terms_and_conditions").on('click', function(ev){
        if ($('#terms_and_conditions:checked').length != 0) {
            $payment.find('button').removeAttr('disabled');
        }
        else {
            $payment.find('button').attr('disabled','disabled');
        }
    });
    
    

    $payment.on('click','button[type="submit"],button[name="submit"]', function(ev) {
       if ($('#terms_and_conditions:checked').length == 0) {
        window.alert('Please agree with Terms and Conditions to continue.');
        } 
    }); 
    

});



$(document).ready(function() {
    $("div.home_tab_menu>div.list-group>a").click(function(e) {
        e.preventDefault();
        $(this).siblings('a.active').removeClass("active");
        $(this).addClass("active");
        var index = $(this).index();
    });
});

function formValidate() {
    var password = $("input[name='password']");
    var confirm_password = $("input[name='confirm_password']");
    if (confirm_password.val() != "") {
        if(password.val() != confirm_password.val()) {
            window.alert("Passwords Don't Match");
            confirm_password.focus();
            return false;
        }
    }
}

function pwReset(home_user, partner_id, token) {
    openerp.jsonRpc("/home/contact/pw_reset", "call", {
        'home_user': home_user,
        'partner_id': partner_id,
        'token': token
    }).done(function(data){
        window.alert(data);
    });
}

$("select[name='bank_type']").live("change",function(){
    if($(this).val() == "iban") {
        console.log('Iban choosen');
    }
});

$("#use_parent_address").live("change",function(){
    if($(this).is(":checked")) {
        $(this).closest('.tab-pane.fade').find("div[id^='child_street_']").addClass("hidden");
        $(this).closest('.tab-pane.fade').find("div[id^='child_street2_']").addClass("hidden");
        $(this).closest('.tab-pane.fade').find("div[id^='child_zip_']").addClass("hidden");
        $(this).closest('.tab-pane.fade').find("div[id^='child_city_']").addClass("hidden");
        $(this).closest('.tab-pane.fade').find("div[id^='child_country_id_']").addClass("hidden");
    }
    if(!$(this).is(":checked")) {
        $(this).closest('.tab-pane.fade').find("div[id^='child_street_']").removeClass("hidden");
        $(this).closest('.tab-pane.fade').find("div[id^='child_street2_']").removeClass("hidden");
        $(this).closest('.tab-pane.fade').find("div[id^='child_zip_']").removeClass("hidden");
        $(this).closest('.tab-pane.fade').find("div[id^='child_city_']").removeClass("hidden");
        $(this).closest('.tab-pane.fade').find("div[id^='child_country_id_']").removeClass("hidden");
    }
});


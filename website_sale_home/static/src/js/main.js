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

$("select[name='bank_type']").live("change",function(){
    if($(this).val() == "iban") {
        console.log('Iban choosen');
    }
});

//~ $("#is_company").live("change",function(){
    //~ if($(this).is(":checked")) {
        //~ $("#is_company_number").removeClass("hidden");
        //~ $("#label_company_name").removeClass("hidden");
        //~ $("#label_name").addClass("hidden");
    //~ }
    //~ if(!$(this).is(":checked")) {
        //~ $("#is_company_number").addClass("hidden");
        //~ $("#label_name").removeClass("hidden");
        //~ $("#label_company_name").addClass("hidden");
    //~ }
//~ });


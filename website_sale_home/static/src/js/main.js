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
    console.log(password.val());
    if(password.val() != confirm_password.val()) {
        window.alert("Passwords Don't Match");
        confirm_password.focus();
        return false;
    }
}

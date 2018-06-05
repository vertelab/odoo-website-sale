$(document).ready(function() {
    $("div.home_tab_menu>div.list-group>a").click(function(e) {
        e.preventDefault();
        $(this).siblings('a.active').removeClass("active");
        $(this).addClass("active");
        var index = $(this).index();
    });
    $("#oe_sale_home_open_msgbox").click(function(){
        $(this).closest('#oe_sale_home_message_box').find("#oe_sale_home_msgbox").removeClass('hidden');
        $(this).addClass('hidden');
        $(this).closest('#oe_sale_home_message_box').find("#oe_sale_home_close_msgbox").removeClass('hidden');
        $(this).closest('#oe_sale_home_message_box').find("#oe_sale_home_send_msgbox").removeClass('hidden');
    });
    $("#oe_sale_home_close_msgbox").click(function(){
        $(this).closest('#oe_sale_home_message_box').find("#oe_sale_home_msgbox").addClass('hidden');
        $(this).closest('#oe_sale_home_message_box').find("#oe_sale_home_send_msgbox").addClass('hidden');
        $(this).addClass('hidden');
        $(this).closest('#oe_sale_home_message_box').find("#oe_sale_home_open_msgbox").removeClass('hidden');
    });
    $("#oe_sale_home_send_msgbox").click(function(){
        var self = $(this);
        openerp.jsonRpc("/home/send_message", "call", {
            "partner_id": self.data('value'),
            "msg_body": self.closest("#oe_sale_home_message_box").find("#oe_sale_home_msgbox").val()
        }).done(function(data){
            $("#oe_sale_home_message_box").load(location.href + " #oe_sale_home_message_box");
            $("#oe_sale_home_msgbox").addClass('hidden');
            $("#oe_sale_home_send_msgbox").addClass('hidden');
            $("#oe_sale_home_close_msgbox").addClass('hidden');
            $("#oe_sale_home_open_msgbox").removeClass('hidden');
        });
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

$('#delUserModal').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget); // Button that triggered the modal
    name = button.data('partner-name');
    var modal = $(this);
    modal.find('.modal-title').text(openerp._t('Delete ') + name);
    modal.find('.delUserModalForm').prop('action', button.data('modal-form-action')); // wont work for some reason
    console.log(button.data('modal-form-action'))
})

function pwReset(home_user, partner_id) {
    openerp.jsonRpc("/home/contact/pw_reset", "call", {
        'home_user': home_user,
        'partner_id': partner_id,
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


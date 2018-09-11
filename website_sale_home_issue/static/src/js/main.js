function loadHomeIssueMessageBox() {
    $("#oe_sale_home_open_msgbox").click(function(){
        $(this).closest('#oe_sale_home_message_box').find("#oe_sale_home_issue_send_msgbox").removeClass('hidden');
    });
    $("#oe_sale_home_close_msgbox").click(function(){
        $(this).closest('#oe_sale_home_message_box').find("#oe_sale_home_issue_send_msgbox").addClass('hidden');
    });
    $("#oe_sale_home_issue_send_msgbox").click(function(){
        $('html,body').css('cursor', 'wait');
        var self = $(this);
        var issue = $("div#issue_info").data("issue_id");
        var issue_id = 0;
        if (issue !== undefined) {
            issue_id = parseInt(issue);
        }
        openerp.jsonRpc("/home/issue/send_message", "call", {
            "issue_id": issue_id,
            "partner_id": self.data('value'),
            "msg_body": self.closest("#oe_sale_home_message_box").find("#oe_sale_home_msgbox").val()
        }).done(function(data){
            $("#oe_sale_home_message_box_history").load(" #oe_sale_home_message_box_history > *");
            $('html,body').css('cursor', 'default');
        });
    });
};

$(document).ready(function() {
    loadHomeIssueMessageBox();
});

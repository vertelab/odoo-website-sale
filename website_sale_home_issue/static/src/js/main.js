function loadHomeIssueMessageBox() {
    $("#oe_issue_open_msgbox").click(function(){
        $(this).addClass('hidden');
        $(this).closest('#oe_issue_message_box').find("#oe_issue_msgbox").removeClass('hidden');
        $(this).closest('#oe_issue_message_box').find("#oe_issue_close_msgbox").removeClass('hidden');
        $(this).closest('#oe_issue_message_box').find("#oe_issue_send_msgbox").removeClass('hidden');
    });
    $("#oe_issue_close_msgbox").click(function(){
        $(this).addClass('hidden');
        $(this).closest('#oe_issue_message_box').find("#oe_issue_msgbox").addClass('hidden');
        $(this).closest('#oe_issue_message_box').find("#oe_issue_open_msgbox").removeClass('hidden');
        $(this).closest('#oe_issue_message_box').find("#oe_issue_send_msgbox").addClass('hidden');
    });
    $("#oe_issue_send_msgbox").click(function(){
        var self = $(this);
        var issue = $("div#issue_info").data("issue_id");
        var issue_id = 0;
        if (issue !== undefined) {
            issue_id = parseInt(issue);
        }
        var $textarea = self.closest("#oe_issue_message_box").find("#oe_issue_msgbox");
        var msg = $textarea.val();
        $textarea.val("");
        $('html,body').css('cursor', 'wait');
        openerp.jsonRpc("/home/issue/send_message", "call", {
            "issue_id": issue_id,
            "partner_id": self.data('value'),
            "msg_body": msg
        }).done(function(data){
            if (data == 'new') {
                window.location.reload();
            }
            else {
                $("#oe_issue_message_box_history").load(" #oe_issue_message_box_history > *");
            }
            $('html,body').css('cursor', 'default');
        });
    });
};

$(document).ready(function() {
    loadHomeIssueMessageBox();
});

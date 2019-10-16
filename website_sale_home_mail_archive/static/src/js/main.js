$(document).ready(function() {
    $('.website-home-filter-button').on('click', function (event) {
        self = $(this);
        var input = $(self.data('target'));
        if (self.hasClass('active')) {
            input.val('');
        } else {
            input.val('1');
        }
        input.parent('form').submit();
    })
});

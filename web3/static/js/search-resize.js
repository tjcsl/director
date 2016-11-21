$(document).ready(function() {
    function checkWidth() {
        var windowsize = $(window).width();
        if(windowsize > 576) {
            $(".search-box").insertBefore("#user-dropdown");
            $(".main").css("padding-top", "40px");
        }
        else {
            $("#user-dropdown").insertBefore(".search-box");
            $(".main").css("padding-top", "80px");
        }
    }
    checkWidth();
    $(window).resize(function() {
        checkWidth();
    });
});

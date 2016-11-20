$(document).ready(function() {
    function checkWidth() {
        var windowsize = $(window).width();
        if(windowsize > 576) {
            $(".search-box").insertBefore("#user-dropdown");
        }
        else {
            $("#user-dropdown").insertBefore(".search-box");
        }
    }
    checkWidth();
    $(".main").css("padding-top", $(".navbar").height().toString() + "px");
    $(window).resize(function() {
        checkWidth();
        $(".main").css("padding-top", $(".navbar").height().toString() + "px");
    });
});

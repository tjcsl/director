$(document).ready(function() {
    $("[data-toggle='tooltip']").each(function() {
        var v = $(this);
        var text = "";
        if (v.hasClass("tag-git")) {
            text = "This user has connected a GitHub account.";
        }
        v.tooltip({
            title: text,
            placement: "left"
        });
    });
});

$(document).ready(function() {
    $("[data-toggle='tooltip']").each(function() {
        var v = $(this);
        var text = "";
        if (v.hasClass("tag-git")) {
            text = "This site uses git for version control.";
        }
        else if (v.hasClass("tag-database")) {
            text = "This site has a database associated with it.";
        }
        else if (v.hasClass("tag-vm")) {
            text = "This site has a virtual machine associated with it.";
        }
        else if (v.hasClass("tag-nginx")) {
            text = "This site has a custom nginx configuration.";
        }
        else if (v.hasClass("tag-nousers")) {
            text = "There are no users, other than administrators, that can access this site.";
        }
        else if (v.hasClass("tag-admin")) {
            text = "You can see this website because you are an administrator.";
        }
        v.tooltip({
            title: text,
            placement: "left"
        });
    });
});

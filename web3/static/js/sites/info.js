jQuery.fn.selectText = function(){
   var doc = document;
   var element = this[0];
   if (doc.body.createTextRange) {
       var range = document.body.createTextRange();
       range.moveToElementText(element);
       range.select();
   } else if (window.getSelection) {
       var selection = window.getSelection();        
       var range = document.createRange();
       range.selectNodeContents(element);
       selection.removeAllRanges();
       selection.addRange(range);
   }
};

$(document).ready(function() {
    if (window.location.hash) {
        var ele = $("a[href='" + window.location.hash + "']");
        if (ele.length && ele.hasClass("nav-link")) {
            ele.click();
        }
    }
    $("#git-pull").click(function() {
        $(this).html("<i class='fa fa-cog fa-spin'></i> Pulling...").prop("disabled", true);
        $.get(git_pull_endpoint, function(data) {
            $("#git-output").text("Process exited with return code " + data.ret + (data.out ? "\n\n" + data.out : "") + (data.err ? "\n\n" + data.err : "")).slideDown("fast");
        }).fail(function(xhr, textStatus, err) {
            $("#git-output").text("Failed to contact server!\n\n" + xhr + "\n" + textStatus + "\n" + err).slideDown("fast");
        }).always(function() {
            $("#git-pull").html("<i class='fa fa-github'></i> Git Pull").prop("disabled", false);
        });
    });
    $("#generate-database-password").click(function(e) {
        if (!confirm("Are you sure you want to regenerate passwords for this database?")) {
            e.preventDefault();
        }
    });
    $("#generate-key").click(function(e) {
        if ($(this).text().indexOf("Regenerate") > -1) {
            if (!confirm("Are you sure you want to regenerate keys for this site?")) {
                e.preventDefault();
            }
        }
    });

    $("#database-url").click(function() {
        $("#database-pass").removeClass("hide");
        $(this).selectText();
    }).on("blur",function() {
        $("#database-pass").addClass("hide");
    }).keydown(function(event) {
        // prevent from entering text
        return (event.ctrlKey || (33 <= event.keyCode && event.keyCode <= 40));
    }).keyup(function(event) {
        event.preventDefault();
    });
});
var select = function(el) {
    var range = document.createRange();
    range.selectNodeContents(el);
    var sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
}

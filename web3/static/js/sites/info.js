/* global
       status_refresh_endpoint
       git_pull_endpoint
       add_ssl_endpoint
*/

jQuery.fn.selectText = function() {
    var doc = document;
    var element = this[0];
    var range;
    if (doc.body.createTextRange) {
        range = document.body.createTextRange();
        range.moveToElementText(element);
        range.select();
    } else if (window.getSelection) {
        var selection = window.getSelection();
        range = document.createRange();
        range.selectNodeContents(element);
        selection.removeAllRanges();
        selection.addRange(range);
    }
};

function updateStatus() {
    var s = $("#process-status").text();
    if (s.includes("STARTING")) {
        setTimeout(function() {
            $.get(status_refresh_endpoint, function(data) {
                $("#process-status").text(data);
                updateStatus();
            });
        }, 1000);
    }
}

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
    $(".generate-cert").submit(function(e) {
        e.preventDefault();
        var t = $(this);
        $.post(add_ssl_endpoint, $(this).serialize(), function() {
            Messenger().info("Sent request to generate certificate. Check back later to see if it worked.");
            t.prop("disabled", true);
        });
    });

    $("#database-url").click(function() {
        $("#database-pass").removeClass("hide");
    }).dblclick(function() {
        $(this).selectText();
    }).on("blur", function() {
        $("#database-pass").addClass("hide");
    });

    updateStatus();
});

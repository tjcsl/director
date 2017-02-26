$(document).ready(function() {
    var consoles = $("#sql-console-wrapper .sql-console");
    consoles.each(function() {
        registerConsole($(this));
    });
});

function registerConsole(console) {
    console.click(function() {
        var sel = window.getSelection().toString();
        if (!sel) {
            $(this).find(".input").focus();
        }
    });
    var history = [];
    var history_point = 0;
    console.keydown(function(e) {
        if (e.which == 38) {
            history_point += 1;
            if (history_point < history.length) {
                $(this).find(".input").val(history[history_point]);
            }
            else {
                history_point = history.length - 1;
            }
            e.preventDefault();
        }
        if (e.which == 40) {
            history_point -= 1;
            if (history_point >= 0 && history.length > 0) {
                $(this).find(".input").val(history[history_point]);
            }
            else {
                $(this).find(".input").val("");
                history_point = -1;
            }
            e.preventDefault();
        }
    });
    console.find(".input").keydown(function(e) {
        var console = $(this).closest(".sql-console");
        if (e.ctrlKey && e.keyCode == 67 && !window.getSelection().toString()) {
            console.find(".output").append(console.find(".ps").text() + $(this).val() + "^C\n");
            $(this).val("");
            console.scrollTop(console[0].scrollHeight);
            e.preventDefault();
        }
    });
    console.find(".input").keypress(function(e) {
        var console = $(this).closest(".sql-console");
        if (e.which == 13) {
            var val = $(this).val();
            if (val) {
                if (val == "exit" || val == "\\q" || val == ".q") {
                    if (typeof back_endpoint != "undefined") {
                        window.location.href = back_endpoint;
                        return;
                    }
                }
                else if ($.trim(val.toLowerCase()) == "\\! clear") {
                    console.find(".output").text("");
                }
                else {
                    console.find(".output").append(console.find(".ps").text() + val + "\n");
                    console.find("table").hide();
                    $.post(sql_endpoint, {"sql": val}, function(data) {
                        console.find(".output").append($("<div />").text(data).html());
                    }).error(function() {
                        console.find(".output").append("<span style='color:#cc0000'>Server Error</span>\n\n");
                    }).always(function() {
                        console.find("table").show();
                        console.find(".input").focus();
                        console.scrollTop(console[0].scrollHeight);
                    });
                    history.unshift(val);
                    history_point = -1;
                }
                $(this).val("");
            }
            else {
                console.find(".output").append(console.find(".ps").text() + "\n");
            }
            console.scrollTop(console[0].scrollHeight);
        }
    });
    printVersion(console);
}

function printVersion(console) {
    $.post(sql_endpoint, {"version": true}, function(data) {
        console.find(".output").append(data + "\n");
    });
}

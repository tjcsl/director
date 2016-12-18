$(document).ready(function() {
    $("#console").click(function() {
        var sel = window.getSelection().toString();
        if (!sel) {
            $("#console .input").focus();
        }
    });
    var history = [];
    var history_point = 0;
    $(document).keydown(function(e) {
        if (e.which == 38) {
            history_point += 1;
            if (history_point < history.length) {
                $("#console .input").val(history[history_point]);
            }
            else {
                history_point = history.length - 1;
            }
            e.preventDefault();
        }
        if (e.which == 40) {
            history_point -= 1;
            if (history_point >= 0 && history.length > 0) {
                $("#console .input").val(history[history_point]);
            }
            else {
                $("#console .input").val("");
                history_point = -1;
            }
            e.preventDefault();
        }
    });
    $.post(sql_endpoint, {"version": true}, function(data) {
        $("#console .output").append(data + "\n");
    });
    $("#console .input").keydown(function(e) {
        if (e.ctrlKey && e.keyCode == 67 && !window.getSelection().toString()) {
            $("#console .output").append($("#console .ps").text() + $(this).val() + "^C\n");
            $(this).val("");
            $("#console").scrollTop($("#console")[0].scrollHeight);
            e.preventDefault();
        }
    });
    $("#console .input").keypress(function(e) {
        if (e.which == 13) {
            var val = $(this).val();
            if (val) {
                if (val == "exit" || val == "\\q" || val == ".q") {
                    window.location.href = back_endpoint;
                    return;
                }
                else if ($.trim(val.toLowerCase()) == "\\! clear") {
                    $("#console .output").text("");
                }
                else {
                    $("#console .output").append($("#console .ps").text() + val + "\n");
                    $("#console table").hide();
                    $.post(sql_endpoint, {"sql": val}, function(data) {
                        $("#console .output").append($("<div />").text(data).html());
                    }).error(function() {
                        $("#console .output").append("<span style='color:#cc0000'>Server Error</span>\n\n");
                    }).always(function() {
                        $("#console table").show();
                        $("#console .input").focus();
                        $("#console").scrollTop($("#console")[0].scrollHeight);
                    });
                    history.unshift(val);
                    history_point = -1;
                }
                $(this).val("");
            }
            else {
                $("#console .output").append($("#console .ps").text() + "\n");
            }
            $("#console").scrollTop($("#console")[0].scrollHeight);
        }
    });
});

$(document).ready(function() {
    $("#console").click(function() {
        $("#input").focus();
    });
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", csrf_token);
        }
    });
    var history = [];
    var history_point = 0;
    $(document).keydown(function(e) {
        if (e.which == 38) {
            history_point += 1;
            if (history_point < history.length) {
                $("#input").val(history[history_point]);
            }
            else {
                history_point = history.length - 1;
            }
            e.preventDefault();
        }
        if (e.which == 40) {
            history_point -= 1;
            if (history_point >= 0 && history.length > 0) {
                $("#input").val(history[history_point]);
            }
            else {
                $("#input").val("");
                history_point = -1;
            }
            e.preventDefault();
        }
    });
    $.post(sql_endpoint, {"version": true}, function(data) {
        $("#output").append(data + "\n");
    });
    $("#input").keypress(function(e) {
        if (e.which == 13) {
            var val = $(this).val();
            if (val) {
                if (val == "exit" || val == "\\q" || val == ".q") {
                    window.location.href = back_endpoint;
                    return;
                }
                $("#output").append($("#ps").text() + val + "\n");
                $("#console table").hide();
                $.post(sql_endpoint, {"sql": val}, function(data) {
                    $("#output").append(data);
                }).always(function() {
                    $("#console table").show();
                    $("#input").focus();
                    $("#console").scrollTop($("#console")[0].scrollHeight);
                });
                history.unshift(val);
                history_point = -1;
                $(this).val("");
            }
            else {
                $("#output").append($("#ps").text() + "\n");
            }
            $("#console").scrollTop($("#console")[0].scrollHeight);
        }
    });
});

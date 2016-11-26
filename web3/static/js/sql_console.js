$(document).ready(function() {
    $("#console").click(function() {
        $("#input").focus();
    });
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", csrf_token);
        }
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
                $(this).val("");
            }
            else {
                $("#output").append($("#ps").text() + "\n");
            }
            $("#console").scrollTop($("#console")[0].scrollHeight);
        }
    });
});

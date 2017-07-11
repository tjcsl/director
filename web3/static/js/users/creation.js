$(document).ready(function() {
    $("#id_username").on("paste keyup blur", function() {
        var new_name = $(this).val();
        var current_email = $("#id_email").val();
        if (!current_email || current_email.includes("@tjhsst.edu")) {
            if (new_name) {
                $("#id_email").val(new_name + "@tjhsst.edu");
            }
            else {
                $("#id_email").val("");
            }
        }
    });
});

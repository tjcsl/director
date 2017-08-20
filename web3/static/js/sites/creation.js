/* global project_domain */
$(document).ready(function() {
    $("#id_name").on("keydown", function(e) {
        if (e.which < 32 || e.which == 127) {
            return;
        }
        if (!(e.key.match(/[A-Za-z0-9_-]{1}/))) {
            e.preventDefault();
        }
    }).on("paste keyup blur", function() {
        var is_project = $("#id_purpose").val() == "project";
        var new_name = $(this).val();
        var current_domain = $("#id_domain").val();
        var domain = ".sites.tjhsst.edu";
        if (is_project) {
            domain = "." + project_domain;
        }
        if (!current_domain || current_domain.includes(domain)) {
            if (new_name) {
                $("#id_domain").val(new_name + domain);
            }
            else {
                $("#id_domain").val("");
            }
        }
    });
    $("form").submit(function() {
        $(this).find("button[type='submit']").prop("disabled", true);
    });
});

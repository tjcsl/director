$(document).ready(function() {
    $("#id_name").on("keydown", function(e) {
        if(e.which < 32 || e.which == 127) return;
        if (!(e.key.match(/[A-Za-z0-9_-]{1}/))) {
            e.preventDefault();
        }
    }).on("paste keyup blur", function(e) {
        var new_name = $(this).val();
        var current_domain = $("#id_domain").val();
        if (!current_domain || current_domain.includes(".sites.tjhsst.edu")) {
            if (new_name) {
                $("#id_domain").val(new_name + ".sites.tjhsst.edu");
            }
            else {
                $("#id_domain").val("");
            }
        }
    });
});

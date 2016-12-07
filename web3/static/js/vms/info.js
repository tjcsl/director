$(document).ready(function() {
    $("form").submit(function(e) {
        $(this).find("button").prop("disabled", true);
        $(this).find("button .fa").removeClass().addClass("fa fa-cog fa-spin");
    });
});

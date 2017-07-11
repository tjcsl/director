$(document).ready(function() {
    $("form").submit(function() {
        $(this).find("button").prop("disabled", true);
        $(this).find("button .fa").removeClass().addClass("fa fa-cog fa-spin");
    });
});

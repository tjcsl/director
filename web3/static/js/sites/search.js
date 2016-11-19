$(document).ready(function() {
    $("#select-site").on("input", function(){
        var val = $(this).val().toLowerCase();
        $("#sites .site").each(function(k, v) {
            var name = $(this).find(".name").text();
            var desc = $(this).find(".desc").text();
            if (desc.toLowerCase().includes(val) || name.toLowerCase().includes(val)) {
                $(this).show();
            }
            else {
                $(this).hide();
            }
        });
    });
});

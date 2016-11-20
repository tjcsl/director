$(document).ready(function() {
    $("#select-user").on("input", function(){
        var val = $(this).val().toLowerCase();
        $("#users .user").each(function(k, v) {
            var name = $(this).find(".name").text();
            if (name.toLowerCase().includes(val)) {
                $(this).show();
            }
            else {
                $(this).hide();
            }
        });
    });
});

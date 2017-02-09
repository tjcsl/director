$(document).ready(function() {
    $("form").submit(function(e) {
        e.preventDefault();
        $("form button, form textarea").prop("disabled", true);
        $("form button").html("<i class='fa fa-cog fa-spin'></i> Processing...");
        var students = $("#students").val().split("\n");
        var create_webdocs = function() {
            var students = students.splice(0, 10).join("\n");
            $.post("?json", { students: students, legacy: !!$("#legacy-checkbox").val(), "no-user": !!$("#no-user-checkbox").val() }, function(data) {
                $.each(data.success, function(k, v) {
                    var item = $("<div class='yes' />");
                    item.text(v);
                    $("#success-list").append(item);
                });
                $.each(data.failure, function(k, v) {
                    var item = $("<div class='no' />");
                    item.text(v);
                    $("#failure-list").append(item);
                });
                if (students.length) {
                    create_webdocs();
                }
                else {
                    $("form").hide();
                    $("#finished-container").show();
                }
            }).fail(function() {
                Messenger().error("An error occured while creating webdocs.");
                $.each(students, function(k, v) {
                    var item = $("<div class='none' />");
                    item.text(v);
                    $("#failure-list").append(item);
                });
                $("form").hide();
                $("#finished-container").show();
            });
        };
        create_webdocs();
    });
});

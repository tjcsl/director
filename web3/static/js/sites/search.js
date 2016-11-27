$(document).ready(function() {
    $("#select-site").on("input", function(){
        var val = $(this).val().toLowerCase();
        var tags = [];
        var matches = val.match(/tag:\w+/g);
        if (matches) {
            $.each(matches, function(k, v) {
                tags.push(v.substring(4).toLowerCase());
            });
        }
        val = $.trim(val.replace(/\s*tag:\w+/g, ""));
        $("#sites .site").each(function(k, v) {
            var name = $(this).find(".name").text();
            var desc = $(this).find(".desc").text();
            var type = $(this).find(".type").text();
            var show = true;
            if (tags.length) {
                var site_tags = [];
                $(this).find(".tag").each(function(k, v) {
                    site_tags.push($(this).text().replace(/\W/g, "").toLowerCase());
                });
                show = false;
                $.each(tags, function(k, v) {
                    $.each(site_tags, function(k2, v2) {
                        if (v2.indexOf(v) == 0) {
                            show = true;
                            return false;
                        }
                    });
                });
            }
            if (show && (desc.toLowerCase().includes(val) || name.toLowerCase().includes(val) || type.toLowerCase().includes(val))) {
                $(this).show();
            }
            else {
                $(this).hide();
            }
        });
    });
});

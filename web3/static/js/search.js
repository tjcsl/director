$(document).ready(function() {
    $(".search-box").on("input", function(){
        var val = $(this).val().toLowerCase();

        var notags = [];
        var nomatches = val.match(/notag:\w+/g);
        if (nomatches) {
            $.each(nomatches, function(k, v) {
                notags.push(v.substring(6).toLowerCase());
            });
        }
        val = $.trim(val.replace(/\s*notag:\w+/g, ""));

        var tags = [];

        var show_online = false;
        var show_offline = false;

        var matches = val.match(/tag:\w+/g);
        if (matches) {
            $.each(matches, function(k, v) {
                var tag = v.substring(4).toLowerCase();
                if (tag == "online") {
                    show_online = true;
                }
                else if (tag == "offline") {
                    show_offline = true;
                }
                else {
                    tags.push(tag);
                }
            });
        }
        val = $.trim(val.replace(/\s*tag:\w+/g, ""));

        matches = val.match(/type:\w+/g);
        var types = [];
        if (matches) {
            $.each(matches, function(k, v) {
                types.push(v.substring(5).toLowerCase());
            });
        }
        val = $.trim(val.replace(/\s*type:\w+/g, ""));

        var search_objects = $(this).data("search");
        var search_fields = $(this).data("fields").split(",");
        $(search_objects).each(function(k, v) {
            var t = $(this);
            var fields = $.map(search_fields, function(val, i) {
                return t.find(val).text().toLowerCase();
            });
            var show = true;
            var site_tags = null;
            if (tags.length || notags.length) {
                site_tags = [];
                $(this).find(".tag").each(function(k, v) {
                    site_tags.push($(this).text().replace(/\W/g, "").toLowerCase());
                });
            }
            if (tags.length) {
                show = false;
                $.each(tags, function(k, v) {
                    $.each(site_tags, function(k2, v2) {
                        if (v2.indexOf(v) != -1) {
                            show = true;
                            return false;
                        }
                    });
                });
            }
            if (notags.length) {
                $.each(notags, function(k, v) {
                    $.each(site_tags, function(k2, v2) {
                        if (v2.indexOf(v) != -1) {
                            show = false;
                            return false;
                        }
                    });
                });
            }
            var matches = false;
            $.each(fields, function(k, v) {
                if (v.includes(val)) {
                    matches = true;
                    return false;
                }
            });
            if (show_offline) {
                if (!$(this).find(".fa.pull-left span").hasClass("red")) {
                    show = false;
                }
            }
            if (show_online) {
                if (!$(this).find(".fa.pull-left span").hasClass("green")) {
                    show = false;
                }
            }
            if (types) {
                var cmpObj = $(this).find(".fa.pull-left");
                var cmp = "other";
                if (cmpObj.hasClass("fa-user")) {
                    cmp = "user";
                }
                else if (cmpObj.hasClass("fa-snowflake")) {
                    cmp = "legacy";
                }
                else if (cmpObj.hasClass("fa-globe")) {
                    cmp = "activity";
                }
                if (types.indexOf(cmp) == -1) {
                    show = false;
                }
            }
            if (show && matches) {
                $(this).show();
            }
            else {
                $(this).hide();
            }
        });
        var sites_shown = $(search_objects + ":visible").length;
        var sites_total = $(search_objects).length;
        if (sites_shown < sites_total) {
            $("#filtered").html("(<b>" + sites_shown + "</b> shown out of <b>" + sites_total + "</b>)");
        }
        else {
            $("#filtered").html("");
        }
    });
});

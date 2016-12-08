$(document).ready(function() {
    $("#select-vm").on("input", function(){
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
        $("#vms .vm").each(function(k, v) {
            var name = $(this).find(".name").text();
            var sub = $(this).find(".sub").text();
            var show = true;
            var vm_tags = null;
            if (tags.length || notags.length) {
                vm_tags = [];
                $(this).find(".tag").each(function(k, v) {
                    vm_tags.push($(this).text().replace(/\W/g, "").toLowerCase());
                });
            }
            if (tags.length) {
                show = false;
                $.each(tags, function(k, v) {
                    $.each(vm_tags, function(k2, v2) {
                        if (v2.indexOf(v) != -1) {
                            show = true;
                            return false;
                        }
                    });
                });
            }
            if (notags.length) {
                $.each(notags, function(k, v) {
                    $.each(vm_tags, function(k2, v2) {
                        if (v2.indexOf(v) != -1) {
                            show = false;
                            return false;
                        }
                    });
                });
            }
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
            if (show && (sub.toLowerCase().includes(val) || name.toLowerCase().includes(val))) {
                $(this).show();
            }
            else {
                $(this).hide();
            }
        });
    });
});

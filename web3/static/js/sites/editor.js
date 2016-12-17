var editor;

$(document).ready(function() {
    var tabs = {};
    var modelist = ace.require("ace/ext/modelist");
    editor = ace.edit("editor");
    editor.setOptions({
        "fontSize": "12pt",
        "showPrintMargin": false
    });
    editor.on("input", function() {
        var tab = $("#tabs .tab.active");
        if (tab.length) {
            tab.toggleClass("unsaved", !editor.session.getUndoManager().isClean());
        }
    });
    editor.setTheme("ace/theme/chrome");
    $(document).keydown(function(e) {
        if (((e.which == 115 || e.which == 83) && e.ctrlKey) || e.which == 19) {
            editor.session.getUndoManager().markClean();
            e.preventDefault();
            e.stopPropagation();
        }
    });
    $("#tabs").on("click", ".tab", function(e) {
        var t = $(this);
        $("#tabs .tab").removeClass("active");
        t.addClass("active");
        var filepath = t.attr("data-file");
        editor.setSession(tabs[filepath]);
        e.preventDefault();
    });
    $("#tabs").on("click", ".tab .fa-times", function(e) {
        e.preventDefault();
        e.stopPropagation();
        var t = $(this).parent();
        delete tabs[t.attr("data-file")];
        t.remove();
        $("#tabs .tab:first").click();
    });
    $("#files").on("click", ".file", function(e) {
        e.preventDefault();
        var t = $(this);
        var filepath = get_path(t) + t.attr("data-name");
        var existing_tab = $("#tabs .tab[data-file='" + filepath.replace("'", "\\'") + "']");
        if (existing_tab.length) {
            existing_tab.click();
        }
        else {
            $.get(load_endpoint + "?name=" + encodeURIComponent(filepath), function(data) {
                if (data.error) {
                    Messenger().error(data.error);
                }
                else {
                    var session = ace.createEditSession(data.contents);
                    session.setMode(modelist.getModeForPath(t.attr("data-name")).mode);
                    editor.setSession(session);
                    $("#tabs .tab").removeClass("active");
                    var tab = $("<div />");
                    tab.addClass("tab active");
                    tab.text(t.attr("data-name"));
                    tab.attr("data-file", filepath);
                    tab.prepend("<i class='fa fa-circle'></i> ");
                    tab.append(" <i class='fa fa-times'></i>");
                    tabs[filepath] = session;
                    $("#tabs").append(tab);
                }
            });
        }
    });
    $("#files").on("click", ".folder", function(e) {
        e.preventDefault();
        var t = $(this);
        if (t.hasClass("loaded")) {
            var depth = parseInt(t.attr("data-depth"));
            var contracted = t.find(".exp").hasClass("fa-caret-down");
            var children = t.nextUntil("div.folder[data-depth=" + depth + "]");
            if (contracted) {
                t.find(".exp").removeClass("fa-caret-down").addClass("fa-caret-up");
                children.show();
                children.find(".exp").each(function(k, v) {
                    var folder = $(this).parent();
                    var expand = folder.find(".exp").hasClass("fa-caret-up");
                    var children = folder.nextUntil("div.folder[data-depth=" + folder.attr("data-depth") + "]").filter(function(v) { return parseInt($(this).attr("data-depth")) > parseInt(folder.attr("data-depth")); });
                    if (!expand) {
                        children.hide();
                    }
                });
            }
            else {
                t.find(".exp").removeClass("fa-caret-up").addClass("fa-caret-down");
                children.filter(function(v) { return parseInt($(this).attr("data-depth")) > depth; }).hide();
            }
        }
        else {
            var depth = parseInt(t.attr("data-depth"));
            var loop_depth = depth;
            var loop_path = "";
            var loop_t = t;
            while (true) {
                loop_depth -= 1;
                if (loop_depth < 0) {
                    break;
                }
                var new_t = loop_t.prevAll("div.folder[data-depth=" + loop_depth + "]:first");
                loop_path = new_t.attr("data-name") + "/" + loop_path;
                loop_t = new_t;
            }
            t.addClass("loaded");
            $.get(path_endpoint + "?path=" + encodeURIComponent(loop_path + t.attr("data-name")), function(data) {
                if (data.error) {
                    Messenger().error(data.error);
                }
                else {
                    $.each(data.files, function(k, v) {
                        var c = (v.type == "f" ? "file" : "folder");
                        var node = $("<div style='padding-left:" + (depth + 1)*20 + "px'><i class='fa fa-fw fa-" + c + "-o'></i> " + $("<div />").text(v.name).html() + "</div>");
                        node.addClass(c);
                        node.attr("data-name", v.name);
                        node.attr("data-depth", depth + 1);
                        if (v.type == "d") {
                            node.append(" <i class='exp fa fa-caret-down'>");
                        }
                        t.after(node);
                    });
                    t.find(".exp").removeClass("fa-caret-down").addClass("fa-caret-up");
                }
            });
        }
    });
    $.get(path_endpoint, function(data) {
        if (data.error) {
            Messenger().error(data.error);
        }
        else {
            $.each(data.files, function(k, v) {
                var c = (v.type == "f" ? "file" : "folder");
                var node = $("<div><i class='fa fa-fw fa-" + c + "-o'></i> " + $("<div />").text(v.name).html() + "</div>");
                node.addClass(c);
                node.attr("data-name", v.name);
                node.attr("data-depth", 0);
                if (v.type == "d") {
                    node.append(" <i class='exp fa fa-caret-down'>");
                }
                $("#files").append(node);
            });
            $("div.folder[data-name='public']").click();
        }
    });
});
function get_path(t) {
    var depth = parseInt(t.attr("data-depth"));
    var loop_depth = depth;
    var loop_path = "/";
    var loop_t = t;
    while (loop_depth >= 1) {
        loop_depth -= 1;
        var new_t = loop_t.prevAll("div.folder[data-depth=" + loop_depth + "]:first");
        loop_path = new_t.attr("data-name") + "/" + loop_path;
        loop_t = new_t;
    }
    if (loop_path == "/") {
        loop_path = "";
    }
    return loop_path;
}

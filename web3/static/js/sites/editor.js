var editor;

$(document).ready(function() {
    var tabs = {};
    var modelist = ace.require("ace/ext/modelist");
    var help_session = ace.createEditSession(" ____  _               _             \n\
|  _ \\(_)_ __ ___  ___| |_ ___  _ __ \n\
| | | | | '__/ _ \\/ __| __/ _ \\| '__|\n\
| |_| | | | |  __/ (__| || (_) | |   \n\
|____/|_|_|  \\___|\\___|\\__\\___/|_|   \n\
\n\
Use the panel on the right to select a file to edit.\n\
Press Ctrl + S to save your changes.\n\
\n\
You can right click files and folders for more options.\n\
You can also drag and drop files to folders to upload them.\n\
You can drag files and folders around to move them.");

    editor = ace.edit("editor");
    editor.setSession(help_session);
    editor.setOptions({
        "fontSize": "12pt",
        "showPrintMargin": false
    });
    function checkTabClean() {
        var tab = $("#tabs .tab.active");
        if (tab.length) {
            tab.toggleClass("unsaved", !editor.session.getUndoManager().isClean());
        }
    }
    editor.on("input", function() {
        checkTabClean();
    });
    function triggerDelete(item) {
        var filepath = get_path(item);
        if (item.hasClass("file")) {
            filepath += item.attr("data-name");
        }
        if (confirm("Are you sure you want to delete:\n" + filepath)) {
            $.post(delete_endpoint + "?name=" + encodeURIComponent(filepath), function(data) {
                if (data.error) {
                    Messenger().error(data.error);
                }
                else {
                    if (item.hasClass("folder")) {
                        var depth = parseInt(item.attr("data-depth"));
                        var children = item.nextUntil("div.folder[data-depth=" + depth + "]").filter(function(v) { return parseInt($(this).attr("data-depth")) > depth; });
                        children.remove();
                    }
                    item.remove();
                }
            });
        }
    }
    function triggerCreate(item, type) {
        var filepath = get_path(item);
        var name = prompt("Enter a name for your new " + (type ? "file" : "directory") + ".");
        if (name) {
            $.post(create_endpoint, { name: name, path: filepath, type: (type ? "f" : "d") }, function(data) {
                if (data.error) {
                    Messenger().error(data.error);
                }
                else {
                    if (filepath == "") {
                        $("#files").children().remove();
                        initFiles();
                    }
                    else {
                        var folder = item;
                        if (!item.hasClass("folder")) {
                            folder = item.prevAll("div.folder[data-depth=" + (parseInt(item.attr("data-depth")) - 1) + "]:first");
                        }
                        var depth = parseInt(folder.attr("data-depth"));
                        var children = folder.nextUntil("div.folder[data-depth=" + depth + "]").filter(function(v) { return parseInt($(this).attr("data-depth")) > depth; });
                        children.remove();
                        folder.removeClass("loaded");
                        folder.click();
                    }
                }
            });
        }
    }
    function triggerDownload(item) {
        var filepath = get_path(item);
        if (item.hasClass("file")) {
            filepath += item.attr("data-name");
        }
        $("#download").attr("src", download_endpoint + "?name=" + encodeURIComponent(filepath));
    }
    $.contextMenu({
        "selector": "#files .file",
        build: function(trigger, e) {
            return {
                callback: function(key, options) {
                    if (key == "open") {
                        trigger.click();
                    }
                    if (key == "delete") {
                        triggerDelete(trigger);
                    }
                    if (key == "new_file") {
                        triggerCreate(trigger, true);
                    }
                    if (key == "download") {
                        triggerDownload(trigger);
                    }
                    if (key == "new_folder") {
                        triggerCreate(trigger, false);
                    }
                },
                items: {
                    "open": {name: "Open", icon: "fa-pencil"},
                    "download": {name: "Download", icon: "fa-download"},
                    "sep1": "--------",
                    "rename": {name: "Rename", icon: "fa-pencil-square-o"},
                    "delete": {name: "Delete", icon: "fa-trash-o"},
                    "sep2": "--------",
                    "new_file": {name: "New File", icon: "fa-file"},
                    "new_folder": {name: "New Folder", icon: "fa-folder"}
                }
            };
        },
        events: {
            show: function(opt) {
                this.addClass("active");
            },
            hide: function(opt) {
                this.removeClass("active");
            }
        }
    });
    $.contextMenu({
        "selector": "#files .folder",
        build: function(trigger, e) {
            return {
                callback: function(key, options) {
                    if (key == "toggle") {
                        trigger.click();
                    }
                    if (key == "delete") {
                        triggerDelete(trigger);
                    }
                    if (key == "download") {
                        triggerDownload(trigger);
                    }
                    if (key == "new_file") {
                        triggerCreate(trigger, true);
                    }
                    if (key == "new_folder") {
                        triggerCreate(trigger, false);
                    }
                },
                items: {
                    "toggle": {name: "Toggle", icon: "fa-expand"},
                    "download": {name: "Download as ZIP", icon: "fa-download"},
                    "sep1": "--------",
                    "rename": {name: "Rename", icon: "fa-pencil-square-o"},
                    "delete": {name: "Delete", icon: "fa-trash-o"},
                    "sep2": "--------",
                    "new_file": {name: "New File", icon: "fa-file"},
                    "new_folder": {name: "New Folder", icon: "fa-folder"}
                }
            };
        },
        events: {
            show: function(opt) {
                this.addClass("active");
            },
            hide: function(opt) {
                this.removeClass("active");
            }
        }
    });
    editor.setTheme("ace/theme/chrome");
    $(document).keydown(function(e) {
        if (((e.which == 115 || e.which == 83) && e.ctrlKey) || e.which == 19) {
            var tab = $("#tabs .tab.active");
            if (tab.length) {
                if (tab.hasClass("tab-help")) {
                    Messenger().error("No file selected to save!");
                }
                else {
                    var filepath = tab.attr("data-file");
                    $.post(save_endpoint + "?name=" + encodeURIComponent(filepath), { contents: editor.session.getValue() }, function(data) {
                        if (data.error) {
                            Messenger().error(data.error);
                        }
                        else {
                            editor.session.getUndoManager().markClean();
                            checkTabClean();
                        }
                    });
                }
            }
            e.preventDefault();
            e.stopPropagation();
        }
    });
    $("#tabs").on("click", ".tab", function(e) {
        var t = $(this);
        $("#tabs .tab").removeClass("active");
        t.addClass("active");
        if (t.hasClass("tab-help")) {
            editor.setSession(help_session);
        }
        else {
            var filepath = t.attr("data-file");
            editor.setSession(tabs[filepath]);
        }
        e.preventDefault();
    });
    $("#tabs").on("click", ".tab .fa-times", function(e) {
        e.preventDefault();
        e.stopPropagation();
        var t = $(this).parent();
        delete tabs[t.attr("data-file")];
        t.remove();
        $("#tabs .tab:last").click();
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
            t.addClass("loaded");
            $.get(path_endpoint + "?path=" + encodeURIComponent(get_path(t)), function(data) {
                if (data.error) {
                    Messenger().error(data.error);
                }
                else {
                    $.each(data.files, function(k, v) {
                        var c = (v.type == "f" ? "file" : "folder");
                        var node = $("<div draggable='true' style='padding-left:" + (depth + 1)*20 + "px'><i class='fa fa-fw fa-" + c + "-o'></i> " + $("<div />").text(v.name).html() + "</div>");
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
    function initFiles() {
        $.get(path_endpoint, function(data) {
            if (data.error) {
                Messenger().error(data.error);
            }
            else {
                $.each(data.files, function(k, v) {
                    var c = (v.type == "f" ? "file" : "folder");
                    var node = $("<div draggable='true'><i class='fa fa-fw fa-" + c + "-o'></i> " + $("<div />").text(v.name).html() + "</div>");
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
    }
    initFiles();
});
function get_path(t) {
    var depth = parseInt(t.attr("data-depth"));
    var loop_depth = depth;
    var loop_path = "";
    var loop_t = t;
    while (loop_depth >= 1) {
        loop_depth -= 1;
        var new_t = loop_t.prevAll("div.folder[data-depth=" + loop_depth + "]:first");
        loop_path = new_t.attr("data-name") + "/" + loop_path;
        loop_t = new_t;
    }
    if (t.hasClass("folder")) {
        loop_path += t.attr("data-name");
    }
    return loop_path;
}

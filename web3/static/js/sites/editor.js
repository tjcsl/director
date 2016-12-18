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
    $("#editor").show();
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
        var filepaths = [];
        var items = $("#files div.active");
        items.each(function(k, v) {
            var item = $(this);
            var filepath = get_path(item);
            if (item.hasClass("file")) {
                filepath += item.attr("data-name");
            }
            filepaths.push(filepath);
        });
        if (confirm("Are you sure you want to delete:\n" + filepaths.join("\n"))) {
            $.post(delete_endpoint, { name: filepaths }, function(data) {
                if (data.error) {
                    Messenger().error(data.error);
                }
                else {
                    items.each(function(k, v) {
                        var item = $(this);
                        if (item.hasClass("folder")) {
                            var depth = parseInt(item.attr("data-depth"));
                            getChildren(item).remove();
                        }
                        item.remove();
                    });
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
                        initFiles();
                    }
                    else {
                        var folder = item;
                        if (!item.hasClass("folder")) {
                            folder = item.prevAll("div.folder[data-depth=" + (parseInt(item.attr("data-depth")) - 1) + "]:first");
                        }
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
    function triggerRename(item) {
        var filepath = get_path(item);
        if (item.hasClass("file")) {
            filepath += item.attr("data-name");
        }
        var name = prompt("Enter a new name for the file or directory:\n" + filepath);
        if (name) {
            $.post(rename_endpoint, { name: filepath, newname: name }, function(data) {
                if (data.error) {
                    Messenger().error(data.error);
                }
                else {
                    item.attr("data-name", name);
                    item.find("span").text(name);
                }
            });
        }

    }
    var path_obj;
    $("#files").on("dragstart", "div", function(e) {
        var item = $(this);
        var filepath = get_path(item);
        if (item.hasClass("file")) {
            filepath += item.attr("data-name");
        }
        e.originalEvent.dataTransfer.setData("path", filepath);
        path_obj = item;
    });
    $("#files").on("dragover", function(e) {
        e.preventDefault();
        e.stopPropagation();
        if (e.target !== $("#files")[0]) {
            $(e.target).closest("div").addClass("dragover");
        }
    });
    $("#files").on("dragleave", "div", function(e) {
        $(this).removeClass("dragover");
    });
    $("#files").on("drop", function(e) {
        if (e.target !== $("#files")[0]) {
            $(e.target).closest("div").removeClass("dragover");
        }
        if (e.originalEvent.dataTransfer) {
            if (e.originalEvent.dataTransfer.files.length) {
                e.preventDefault();
                e.stopPropagation();
                var files = e.originalEvent.dataTransfer.files;
                var folder;
                var path = "";
                if (e.target !== $("#files")[0]) {
                    folder = $(e.target).closest("div.folder");
                    if (folder.length) {
                        path = get_path(folder);
                    }
                    else {
                        folder = $(e.target).closest("div.file");
                        if (folder.length) {
                            folder = folder.prevAll("div.folder[data-depth=" + (parseInt(folder.attr("data-depth")) - 1) + "]:first");
                            if (folder.length) {
                                path = get_path(folder);
                            }
                            else {
                                folder = null;
                            }
                        }
                    }
                }
                var formData = new FormData();
                formData.append("path", path);
                for (var i = 0; i < files.length; i++) {
                    formData.append("file[]", files[i], files[i].name);
                }
                $.ajax({
                    url: upload_endpoint,
                    type: "POST",
                    data: formData,
                    processData: false,
                    contentType: false,
                    success: function(data) {
                        if (data.error) {
                            Messenger().error(data.error);
                        }
                        else {
                            if (path == "") {
                                initFiles();
                            }
                            else {
                                var depth = 0;
                                if (folder) {
                                    folder.removeClass("loaded");
                                    folder.click();
                                }
                                else {
                                    initFiles();
                                }
                            }
                        }
                    }
                });
            }
            else {
                var old_path = e.originalEvent.dataTransfer.getData("path");
                if (old_path) {
                    e.preventDefault();
                    e.stopPropagation();
                    var new_path = "";
                    if (e.target !== $("#files")[0]) {
                        var f = $(e.target).closest("div.folder");
                        if (f.length) {
                            new_path = get_path(f);
                        }
                        else {
                            f = $(e.target).closest("div.file");
                            if (f.length) {
                                f = f.prevAll("div.folder[data-depth=" + (parseInt(f.attr("data-depth")) - 1) + "]:first");
                                new_path = get_path(f);
                            }
                            if (!f.length) {
                                f = $("#files");
                            }
                        }
                    }
                    if (old_path != new_path) {
                        $.post(move_endpoint, { old: old_path, new: new_path }, function(data) {
                            if (data.error) {
                                Messenger().error(data.error);
                            }
                            else {
                                if (path_obj.hasClass("folder")) {
                                    var children = getChildren(path_obj);
                                }
                                if (typeof f == "undefined" || f.attr("id") == "files") {
                                    newdepth = 0;
                                    path_obj.insertAfter($("#files div:last"));
                                }
                                else {
                                    var newdepth = parseInt(f.attr("data-depth")) + 1;
                                    var dest_children = getChildren(f);
                                    if (dest_children.length) {
                                        f = dest_children[dest_children.length-1];
                                    }
                                    path_obj.insertAfter(f);
                                }
                                path_obj.css("padding-left", newdepth*20 + "px");
                                path_obj.attr("data-depth", newdepth);
                                if (path_obj.hasClass("folder")) {
                                    $.each(children.get().reverse(), function(k, v) {
                                        var cdepth = newdepth + (parseInt($(this).attr("data-depth")) - depth);
                                        $(this).insertAfter(path_obj);
                                        $(this).attr("data-depth", cdepth);
                                        $(this).css("padding-left", cdepth*20 + "px");
                                    });
                                }
                                path_obj = null;
                            }
                        });
                    }
                }
            }
        }
    });
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
                    if (key == "rename") {
                        triggerRename(trigger);
                    }
                    if (key == "set_process") {
                        var filepath = get_path(trigger) + trigger.attr("data-name");
                        $.post(process_endpoint, {name: filepath}, function(data) {
                            if (data.error) {
                                Messenger().error(data.error);
                            }
                            else {
                                Messenger().success("Dynamic process successfully updated!");
                            }
                        });
                    }
                    if (key == "set_exec") {
                        var filepath = get_path(trigger) + trigger.attr("data-name");
                        $.post(exec_endpoint, {name: filepath}, function(data) {
                            if (data.error) {
                                Messenger().error(data.error);
                            }
                            else {
                                trigger.toggleClass("exec");
                            }
                        });
                    }
                },
                items: {
                    "open": {name: "Open", icon: "fa-pencil"},
                    "download": {name: "Download", icon: "fa-download"},
                    "sep1": "--------",
                    "set_exec": {name: (trigger.hasClass("exec") ? "Unset Executable" : "Set Executable"), icon: "fa-cog"},
                    "set_process": (is_dynamic ? {name: "Set Process", icon: "fa-cogs"} : undefined),
                    "sep2": "--------",
                    "rename": {name: "Rename", icon: "fa-pencil-square-o"},
                    "delete": {name: "Delete", icon: "fa-trash-o"},
                    "sep3": "--------",
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
                $("#files div.active").removeClass("active");
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
                    if (key == "rename") {
                        triggerRename(trigger);
                    }
                    if (key == "refresh") {
                        trigger.removeClass("loaded");
                        var depth = parseInt(trigger.attr("data-depth"));
                        getChildren(trigger).remove();
                        trigger.click();
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
                    "new_folder": {name: "New Folder", icon: "fa-folder"},
                    "sep3": "--------",
                    "refresh": {name: "Refresh", icon: "fa-refresh"}
                }
            };
        },
        events: {
            show: function(opt) {
                this.addClass("active");
            },
            hide: function(opt) {
                $("#files div.active").removeClass("active");
            }
        }
    });
    editor.setTheme("ace/theme/chrome");
    $(document).keydown(function(e) {
        if (((e.which == 115 || e.which == 83) && e.ctrlKey) || e.which == 19) {
            var tab = $("#tabs .tab.active");
            if (tab.length) {
                if (tab.hasClass("tab-help") || tab.hasClass("tab-custom")) {
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
        $(".tab-pane").hide();
        if (t.hasClass("tab-help") || t.attr("data-file")) {
            $("#editor").show();
            if (t.hasClass("tab-help")) {
                editor.setSession(help_session);
            }
            else {
                var filepath = t.attr("data-file");
                editor.setSession(tabs[filepath]);
            }
        }
        else if (t.hasClass("tab-terminal")) {
            if (!$("#terminal iframe").length) {
                var frame = $("<iframe />");
                frame.attr("src", terminal_url);
                $("#terminal").append(frame);
            }
            $("#terminal").show();
        }
        e.preventDefault();
    });
    $("#tabs").on("click", ".tab .fa-times", function(e) {
        e.preventDefault();
        e.stopPropagation();
        var t = $(this).parent();
        delete tabs[t.attr("data-file")];
        t.remove();
        var next_tab = $("#tabs .tab:not(.tab-terminal):last")
        if (next_tab) {
            next_tab.click();
        }
        else {
            $(".tab-pane").hide();
        }
    });
    $("#files").on("click", ".file", function(e) {
        e.preventDefault();
        if (e.ctrlKey) {
            $(this).addClass("active");
            return;
        }
        else {
            $("#files div").removeClass("active");
        }
        var t = $(this);
        var filepath = get_path(t) + t.attr("data-name");
        var existing_tab = $("#tabs .tab[data-file='" + filepath.replace("'", "\\'") + "']");
        if (existing_tab.length) {
            existing_tab.click();
        }
        else {
            $("#tabs .tab").removeClass("active");
            var tab = $("<div />");
            tab.addClass("tab active");
            tab.text(t.attr("data-name"));
            tab.attr("data-file", filepath);
            tab.prepend("<i class='fa fa-circle'></i> ");
            tab.append(" <i class='fa fa-times'></i>");
            $("#tabs").append(tab);
            $.get(load_endpoint + "?name=" + encodeURIComponent(filepath), function(data) {
                if (data.error) {
                    Messenger().error(data.error);
                    tab.remove();
                }
                else {
                    var session = ace.createEditSession(data.contents);
                    session.setMode(modelist.getModeForPath(t.attr("data-name")).mode);
                    editor.setSession(session);
                    tabs[filepath] = session;
                }
            });
        }
    });
    $("#files").on("click", ".folder", function(e) {
        e.preventDefault();
        if (e.ctrlKey) {
            $(this).addClass("active");
            return;
        }
        else {
            $("#files div").removeClass("active");
        }
        var t = $(this);
        if (t.hasClass("loaded")) {
            var contracted = t.find(".fa-fw").hasClass("fa-folder-o");
            var children = getChildren(t);
            if (contracted) {
                t.find(".fa-fw").removeClass("fa-folder-o").addClass("fa-folder-open-o");
                children.show();
                children.find(".fa-fw").each(function(k, v) {
                    var folder = $(this).parent();
                    if (!folder.hasClass("folder")) {
                        return;
                    }
                    var expand = $(this).hasClass("fa-folder-open-o");
                    var children = getChildren(folder);
                    if (!expand) {
                        children.hide();
                    }
                });
            }
            else {
                t.find(".fa-fw").removeClass("fa-folder-open-o").addClass("fa-folder-o");
                children.hide();
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
                        var node = $("<div draggable='true' style='padding-left:" + (depth + 1)*20 + "px'><i class='fa fa-fw fa-" + c + "-o'></i> <span>" + $("<div />").text(v.name).html() + "</span></div>");
                        node.addClass(c);
                        node.attr("data-name", v.name);
                        node.attr("data-depth", depth + 1);
                        if (v.executable) {
                            node.addClass("exec");
                        }
                        if (!getChildren(t).has("div[data-depth=" + (depth + 1) + "][data-name='" + v.name.replace("'", "\\'") + "']").length) {
                            t.after(node);
                        }
                    });
                    t.find(".fa-fw").removeClass("fa-folder-o").addClass("fa-folder-open-o");
                }
            });
        }
    });
    function initFiles(firstRun) {
        firstRun = firstRun || false;
        if (firstRun) {
            $("#files div").remove();
        }
        $.get(path_endpoint, function(data) {
            if (data.error) {
                Messenger().error(data.error);
            }
            else {
                $.each(data.files, function(k, v) {
                    var c = (v.type == "f" ? "file" : "folder");
                    var node = $("<div draggable='true'><i class='fa fa-fw fa-" + c + "-o'></i> <span>" + $("<div />").text(v.name).html() + "</span></div>");
                    node.addClass(c);
                    node.attr("data-name", v.name);
                    node.attr("data-depth", 0);
                    if (v.executable) {
                        node.addClass("exec");
                    }
                    if (!$("#files div[data-depth=0][data-name='" + v.name.replace("'", "\\'") + "']").length) {
                        $("#files").append(node);
                    }
                });
                if (firstRun) {
                    $("div.folder[data-name='public']").click();
                }
            }
        });
    }
    initFiles(true);

    var sep_dragging = false;
    $("#sep").mousedown(function() {
        sep_dragging = true;
    });
    $(document).mouseup(function() {
        sep_dragging = false;
    }).mousemove(function(e) {
        if (sep_dragging) {
            var newPos = e.clientX - 10;
            if (newPos < 25) {
                newPos = 25;
            }
            else {
                var max = $(window).width() - 40;
                if (newPos > max) {
                    newPos = max;
                }
            }
            $("#files").width(newPos);
            $("#editor-wrapper").css("width", "calc(100vw - 20px - " + newPos + "px)");
        }
    });
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
function getChildren(item) {
    var depth = parseInt(item.attr("data-depth"));
    return item.nextUntil(function() {
        return $(this).hasClass("folder") && parseInt($(this).attr("data-depth")) <= depth;
    });
}

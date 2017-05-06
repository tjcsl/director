$(document).ready(function() {
    var modelist = ace.require("ace/ext/modelist");
    ace.require("ace/ext/language_tools");
    var editors = [];
    var settings = {
        "hidden-files": true,
        "prompt-delete": true,
        "layout-theme": "light",
        "editor-theme": "ace/theme/chrome",
        "font-size": 16
    };
    var layout_config = {
        settings: {
            showPopoutIcon: false
        },
        labels: {
            close: "Close",
            maximise: "Maximize",
            minimise: "Minimize"
        },
        content: [{
            type: 'row',
            content: [{
                type: 'component',
                componentName: 'files',
                width: 25,
                isClosable: false
            },{
                type: 'column',
                content: [{
                    type: 'stack',
                    isClosable: false,
                    id: "default-file",
                    content: [{
                        type: 'component',
                        componentName: 'help'
                    }]
                },{
                    type: 'stack',
                    id: "default-terminal",
                    height: 30,
                    content: [{
                        type: 'component',
                        componentName: 'terminal'
                    }, {
                        type: 'component',
                        componentName: 'nginx'
                    }]
                }]
            }]
        }]
    };
    if (typeof registerConsole !== 'undefined') {
        layout_config["content"][0]["content"][1]["content"][1]["content"].push({
            type: 'component',
            componentName: 'sql'
        });
    }

    if (typeof localStorage !== 'undefined') {
        var savedState = localStorage.getItem("editor-state-" + site_name);
        if (savedState) {
            layout_config = JSON.parse(savedState);
            if ("editor" in layout_config) {
                for (var key in layout_config["editor"]) {
                    settings[key] = layout_config["editor"][key];
                }
            }
            Messenger().post({
                "message": "Your editor layout has been restored from your last session.",
                "actions": {
                    "reset": {
                        "label": "Reset Layout",
                        "action": function() {
                            localStorage.removeItem("editor-state-" + site_name);
                            window.location.reload();
                        }
                    }
                },
                "showCloseButton": true
            });
        }
    }

    var layout = new GoldenLayout(layout_config, $("#editor-container"));

    function saveConfig() {
        if (typeof localStorage !== 'undefined') {
            var state = layout.toConfig();
            state["editor"] = settings;
            localStorage.setItem("editor-state-" + site_name, JSON.stringify(state));
        }
    }

    function updateSettings() {
        $(".setting[data-setting='hidden-files']").prop("checked", settings["hidden-files"]);
        $(".setting[data-setting='prompt-delete']").prop("checked", settings["prompt-delete"]);
        $(".setting[data-setting='layout-theme']").val(settings["layout-theme"]);
        $(".setting[data-setting='editor-theme']").val(settings["editor-theme"]);
        $(".setting[data-setting='font-size']").val(settings["font-size"]);

        $("#files").toggleClass("show-hidden", settings["hidden-files"]);
        $("body").toggleClass("dark", settings["layout-theme"] == "dark");
        $("#layout-light").prop("disabled", settings["layout-theme"] != "light");
        $("#layout-dark").prop("disabled", settings["layout-theme"] != "dark");
        $.each(editors, function(k, v) {
            v.setTheme(settings["editor-theme"]);
            v.setFontSize(settings["font-size"] + "px");
        });
    }

    updateSettings();

    $(document).on("change", ".settings-pane .setting", function(e) {
        if ($(this).attr("type") == "checkbox") {
            settings[$(this).attr("data-setting")] = $(this).prop("checked");
        }
        else {
            settings[$(this).attr("data-setting")] = $(this).val();
        }
        updateSettings();
        saveConfig();
    });

    $(document).on("change", ".settings-pane .setting[data-setting='layout-theme']", function(e) {
        if (settings["layout-theme"] == "dark") {
            if (settings["editor-theme"] == "ace/theme/chrome") {
                settings["editor-theme"] = "ace/theme/monokai";
            }
        }
        else {
            if (settings["editor-theme"] == "ace/theme/monokai") {
                settings["editor-theme"] = "ace/theme/chrome";
            }
        }
        updateSettings();
        saveConfig();
    });

    layout.on("stateChanged", function() {
        saveConfig();
    });

    // #files code
    function triggerDelete() {
        var filepaths = [];
        var items = $("#files div.active");
        items.each(function(k, v) {
            var item = $(this);
            var filepath = getPath(item);
            if (item.hasClass("file")) {
                filepath += item.attr("data-name");
            }
            filepaths.push(filepath);
        });
        function doDelete() {
            $.post(delete_endpoint, { name: filepaths }, function(data) {
                if (data.error) {
                    Messenger().error(data.error);
                }
                else {
                    items.each(function(k, v) {
                        var item = $(this);
                        if (item.hasClass("folder")) {
                            getChildren(item).remove();
                        }
                        item.remove();
                    });
                }
            });
        }
        if (settings["prompt-delete"]) {
            modalConfirm("Are you sure you want to delete these files?", "<p>Are you sure you want to delete <b>" + filepaths.length + "</b> file(s):</p><pre>" + $("<div />").text(filepaths.join("\n")).html() + "</pre>", function() {
                doDelete();
            });
        }
        else {
            doDelete();
        }
    }
    function triggerCreate(item, type) {
        if (item[0] == $("#files")[0]) {
            filepath = "";
        }
        else {
            var filepath = getPath(item);
        }
        var name = modalPrompt("New " + (type ? "File" : "Folder"), "Enter a name for your new " + (type ? "file" : "directory") + ".", function(name) {
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
                        folder.dblclick();
                    }
                    if (type) {
                        var newTab = {
                            id: "file-" + join(filepath, name),
                            type: "component",
                            componentName: "file",
                            componentState: { file: name, path: join(filepath, name), isImage: false, isMedia: false }
                        };
                        layout.root.getItemsById("default-file")[0].addChild(newTab);
                    }
                }
            });
        });
    }
    function triggerDownload(item) {
        var filepath = getPath(item);
        if (item.hasClass("file")) {
            filepath += item.attr("data-name");
        }
        var frame = $("<iframe class='download' />");
        frame.load(function() {
            $(this).remove();
        });
        frame.attr("src", download_endpoint + "?name=" + encodeURIComponent(filepath));
        $("body").append(frame);
    }
    function triggerRename(item) {
        var filepath = getPath(item);
        if (item.hasClass("file")) {
            filepath += item.attr("data-name");
        }
        modalPrompt("Rename " + (item.hasClass("file") ? "File" : "Folder"), "Enter a new name for the file or directory:\n" + filepath, function(name) {
            $.post(rename_endpoint, { name: filepath, newname: name }, function(data) {
                if (data.error) {
                    Messenger().error(data.error);
                }
                else {
                    var newNode = makeNode({name: name, type: item.hasClass("file") ? "f" : "d"}, item.attr("data-depth"));
                    item.replaceWith(newNode);
                }
            });
        }, item.attr("data-name"));
    }

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
                var file_set = {};
                $.each(data.files, function(k, v) {
                    file_set[v.name] = true;
                    var node = makeNode(v);
                    if (!$("#files div[data-depth=0][data-name='" + v.name.replace("'", "\\'") + "']").length) {
                        $("#files").append(node);
                    }
                });
                $("#files div[data-depth=0]").each(function() {
                    if (!file_set[$(this).attr("data-name")]) {
                        $(this).remove();
                    }
                });
                if (firstRun) {
                    $("div.folder[data-name='public']").dblclick();
                }
            }
        });
    }
    function registerFileHandlers(files) {
        files.on("dblclick", ".file", function(e) {
            e.preventDefault();
            var t = $(this);
            var filepath = getPath(t) + t.attr("data-name");
            var newTab = {
                id: "file-" + filepath,
                type: "component",
                componentName: "file",
                componentState: { file: t.attr("data-name"), path: filepath, isImage: $(this).hasClass("image"), isMedia: $(this).hasClass("media") }
            };
            var existing = layout.root.getItemsById("file-" + filepath);
            if (existing.length) {
                existing[0].parent.setActiveContentItem(existing[0]);
            }
            else {
                layout.root.getItemsById("default-file")[0].addChild(newTab);
            }
        });
        files.on("click", ".file", function(e) {
            e.preventDefault();
            if (e.ctrlKey) {
                $(this).toggleClass("active");
            }
            else if (e.shiftKey) {
                var depth = $(this).attr("data-depth");
                if ($(this).prevAll(".file.active[data-depth='" + depth + "']").length) {
                    $(this).prevUntil(".file.active[data-depth='" + depth + "']").addClass("active");
                }
                if ($(this).nextAll(".file.active[data-depth='" + depth + "']").length) {
                    $(this).nextUntil(".file.active[data-depth='" + depth + "']").addClass("active");
                }
                $(this).addClass("active");
                return;
            }
            else {
                $("#files div").removeClass("active");
                $(this).addClass("active");
            }
        });
        files.on("dblclick", ".folder", function(e) {
            e.preventDefault();
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
                $.get(path_endpoint + "?path=" + encodeURIComponent(getPath(t)), function(data) {
                    if (data.error) {
                        Messenger().error(data.error);
                    }
                    else {
                        $.each(data.files, function(k, v) {
                            var node = makeNode(v, depth + 1);
                            if (!getChildren(t).filter("div[data-depth=" + (depth + 1) + "][data-name='" + v.name.replace("'", "\\'") + "']").length) {
                                t.after(node);
                            }
                        });
                        t.find(".fa-fw").removeClass("fa-folder-o").addClass("fa-folder-open-o");
                    }
                });
                $(this).trigger("folder:load");
            }
        });
        files.on("click", ".folder", function(e) {
            e.preventDefault();
            if (!e.ctrlKey) {
                $("#files div").removeClass("active");
            }
            $(this).addClass("active");
        });
        var path_obj;
        files.on("dragstart", "div", function(e) {
            var item = $(this);
            var filepath = getPath(item);
            if (item.hasClass("file")) {
                filepath += item.attr("data-name");
            }
            e.originalEvent.dataTransfer.setData("path", filepath);
            path_obj = item;
        });
        files.on("dragover", function(e) {
            e.preventDefault();
            e.stopPropagation();
            if (e.target !== $("#files")[0]) {
                $(e.target).closest("div").addClass("dragover");
            }
        });
        files.on("dragleave", "div", function(e) {
            $(this).removeClass("dragover");
        });
        files.on("drop", function(e) {
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
                            path = getPath(folder);
                        }
                        else {
                            folder = $(e.target).closest("div.file");
                            if (folder.length) {
                                folder = folder.prevAll("div.folder[data-depth=" + (parseInt(folder.attr("data-depth")) - 1) + "]:first");
                                if (folder.length) {
                                    path = getPath(folder);
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
                    var msg = Messenger().info("Uploading " + files.length + " file(s)...");
                    $.ajax({
                        url: upload_endpoint,
                        type: "POST",
                        data: formData,
                        cache: false,
                        processData: false,
                        contentType: false,
                        success: function(data) {
                            if (data.error) {
                                msg.update({
                                    type: "error",
                                    message: data.error
                                });
                            }
                            else {
                                if (path != "" && folder) {
                                    folder.removeClass("loaded");
                                    folder.dblclick();
                                }
                                else {
                                    initFiles();
                                }
                            }
                            msg.update({
                                type: "success",
                                message: "File(s) uploaded!"
                            });
                        },
                        error: function(httpObj, textStatus) {
                            if (httpObj.status == 413) {
                                msg.update({
                                    type: "error",
                                    message: "The file(s) you are trying to upload are too large."
                                });
                            }
                            else {
                                msg.update({
                                    type: "error",
                                    message: "No files were uploaded due to an unknown error."
                                });
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
                                new_path = getPath(f);
                            }
                            else {
                                f = $(e.target).closest("div.file");
                                if (f.length) {
                                    f = f.prevAll("div.folder[data-depth=" + (parseInt(f.attr("data-depth")) - 1) + "]:first");
                                    new_path = getPath(f);
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
                                    var children = getChildren(path_obj);
                                    if (typeof f == "undefined" || f.attr("id") == "files") {
                                        newdepth = 0;
                                        var existing = $("[data-depth=0][data-name='" + path_obj.attr("data-name").replace("'", "\\'") + "']");
                                        if (!existing.length) {
                                            path_obj.insertAfter($("#files div:last"));
                                        }
                                        else {
                                            path_obj = existing;
                                        }
                                    }
                                    else {
                                        if (f.hasClass("folder") && !f.find(".fa-fw").hasClass("fa-folder-open-o")) {
                                            f.dblclick();
                                        }
                                        var newdepth = parseInt(f.attr("data-depth")) + 1;
                                        var dest_children = getChildren(f);
                                        if (dest_children.length) {
                                            f = dest_children[dest_children.length - 1];
                                        }
                                        var existing = dest_children.filter("[data-name='" + path_obj.attr("data-name").replace("'", "\\'") + "']");
                                        if (!existing.length) {
                                            path_obj.insertAfter(f);
                                        }
                                        else {
                                            path_obj = existing;
                                        }
                                    }
                                    var depth = path_obj.attr("data-depth");
                                    path_obj.css("padding-left", newdepth * 20 + "px");
                                    path_obj.attr("data-depth", newdepth);
                                    var existing_children = getChildren(path_obj);
                                    if (path_obj.hasClass("folder")) {
                                        $.each(children.get().reverse(), function(k, v) {
                                            var cdepth = newdepth + (parseInt($(this).attr("data-depth")) - depth);
                                            if (!existing_children.filter("[data-name='" + $(this).attr("data-name").replace("'", "\\'") + "']").length) {
                                                $(this).insertAfter(path_obj);
                                                $(this).attr("data-depth", cdepth);
                                                $(this).css("padding-left", cdepth * 20 + "px");
                                            }
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
    }
    var uploader_folder = null;
    $("#uploader").on("change", function(e) {
        if (!this.files.length) {
            return;
        }
        var formData = new FormData();
        if (uploader_folder) {
            formData.append("path", getPath(uploader_folder));
        }
        else {
            formData.append("path", "");
        }
        for (var i = 0; i < this.files.length; i++) {
            formData.append("file[]", this.files[i], this.files[i].name);
        }
        var msg = Messenger().info("Uploading " + this.files.length + " file(s)...");
        $.ajax({
            url: upload_endpoint,
            type: "POST",
            data: formData,
            cache: false,
            processData: false,
            contentType: false,
            success: function(data) {
                if (data.error) {
                    msg.update({
                        type: "error",
                        message: data.error
                    });
                }
                else {
                    if (uploader_folder) {
                        uploader_folder.removeClass("loaded");
                        uploader_folder.click();
                    }
                    else {
                        initFiles();
                    }
                    msg.update({
                        type: "success",
                        message: "File(s) uploaded!"
                    });
                }
            },
            error: function(httpObj, textStatus) {
                if (httpObj.status == 413) {
                    msg.update({
                        type: "error",
                        message: "The file(s) you are trying to upload are too large."
                    });
                }
                else {
                    msg.update({
                        type: "error",
                        message: "No files were uploaded due to an unknown error."
                    });
                }
            }
        });
    });
    $.contextMenu({
        "selector": "#files",
        build: function(trigger, e) {
            return {
                callback: function(key, options) {
                    if (key == "new_file") {
                        triggerCreate(trigger, true);
                    }
                    if (key == "new_folder") {
                        triggerCreate(trigger, false);
                    }
                    if (key == "refresh") {
                        initFiles();
                    }
                    if (key == "open") {
                        window.open(site_url, "_blank");
                    }
                    if (key == "new_terminal" || key == "new_nginx" || key == "new_sql") {
                        var c = layout.root.getItemsById("default-terminal");
                        if (!c.length) {
                            c = layout.root.getItemsById("default-file");
                        }
                        var newTab = {
                            type: "component",
                            componentName: (key == "new_terminal" ? "terminal" : key == "new_nginx" ? "nginx" : "sql")
                        };
                        c[0].addChild(newTab);
                    }
                    if (key == "new_settings") {
                        var c = layout.root.getItemsById("default-file");
                        var newTab = {
                            type: "component",
                            componentName: "help"
                        };
                        c[0].addChild(newTab);
                    }
                    if (key == "upload") {
                        uploader_folder = null;
                        $("#uploader").trigger("click");
                    }
                    if (key.startsWith("site_type_")) {
                        var type = key.substring(10);
                        $.post(site_type_endpoint, { type: type }, function(data) {
                            if (data.error) {
                                Messenger().error(data.error);
                            }
                            else {
                                is_dynamic = type == "dynamic";
                                Messenger().success("Site type changed to " + type + "!");
                            }
                        });
                    }
                },
                items: {
                    "open": {name: "Open Website", icon: "fa-globe"},
                    "site_type": {
                        name: "Set Site Type",
                        icon: "fa-cogs",
                        items: {
                            "site_type_static": {name: "Static", icon: "fa-cog"},
                            "site_type_php": {name: "PHP", icon: "fa-cog"},
                            "site_type_dynamic": {name: "Dynamic", icon: "fa-cog"}
                        }
                    },
                    "sep1": "--------",
                    "upload": {name: "Upload", icon: "fa-upload"},
                    "new_file": {name: "New File", icon: "fa-file"},
                    "new_folder": {name: "New Folder", icon: "fa-folder"},
                    "sep2": "--------",
                    "new_terminal": {name: "New Terminal", icon: "fa-terminal"},
                    "new_nginx": {name: (is_superuser ? "Edit" : "View") + " Nginx Config", icon: "fa-pencil"},
                    "new_sql": typeof registerConsole == 'undefined' ? undefined : {name: "SQL Console", icon: "fa-database"},
                    "new_settings": {name: "Settings", icon: "fa-wrench"},
                    "sep3": "--------",
                    "refresh": {name: "Refresh", icon: "fa-refresh"}
                }
            };
        },
        events: {
            show: function(opt) {
                $("#files div.active").removeClass("active");
            }
        }
    });
    $.contextMenu({
        "selector": "#files .file",
        build: function(trigger, e) {
            var multiple_selected = $("#files div.file.active").length > 1;
            var is_public = getPath(trigger).startsWith("public/");
            return {
                callback: function(key, options) {
                    if (key == "open") {
                        $("#files div.file.active").dblclick();
                    }
                    if (key == "delete") {
                        triggerDelete();
                    }
                    if (key == "new_file") {
                        triggerCreate(trigger, true);
                    }
                    if (key == "download") {
                        $("#files div.file.active").each(function() {
                            triggerDownload($(this));
                        });
                    }
                    if (key == "new_folder") {
                        triggerCreate(trigger, false);
                    }
                    if (key == "rename") {
                        triggerRename(trigger);
                    }
                    if (key == "set_process") {
                        var filepath = getPath(trigger) + trigger.attr("data-name");
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
                        var paths = [];
                        var fobjs = $("#files div.file.active");
                        fobjs.each(function() {
                            var trigger = $(this);
                            var filepath = getPath(trigger) + trigger.attr("data-name");
                            paths.push(filepath);
                        });
                        $.post(exec_endpoint, {name: paths, on: !trigger.hasClass("exec")}, function(data) {
                            if (data.error) {
                                Messenger().error(data.error);
                            }
                            else {
                                fobjs.toggleClass("exec", !trigger.hasClass("exec"));
                            }
                        });
                    }
                    if (key == "preview") {
                        $("#files div.file.active").each(function() {
                            var fileobj = $(this);
                            var filepath = getPath(fileobj) + fileobj.attr("data-name");
                            if (filepath.startsWith("public/")) {
                                var newTab = {
                                    id: "preview-" + filepath,
                                    type: "component",
                                    componentName: "preview",
                                    componentState: { path: filepath, file: fileobj.attr("data-name") }
                                };
                                var existing = layout.root.getItemsById("preview-" + filepath);
                                if (existing.length) {
                                    existing[0].parent.setActiveContentItem(existing[0]);
                                }
                                else {
                                    layout.root.getItemsById("default-file")[0].addChild(newTab);
                                }
                            }
                            else {
                                Messenger().error("<b>" + $("<div />").text(fileobj.attr("data-name")).html() + "</b> cannot be previewed.");
                            }
                        });
                    }
                    if (key == "open_browser") {
                        $("#files div.file.active").each(function() {
                            var fileobj = $(this);
                            var filepath = getPath(fileobj) + fileobj.attr("data-name");
                            if (filepath.startsWith("public/")) {
                                var final_url = site_url + filepath.replace(/^public\//, "");
                                window.open(final_url, "_blank");
                            }
                            else {
                                Messenger().error("<b>" + $("<div />").text(fileobj.attr("data-name")).html() + "</b> cannot be displayed.");
                            }
                        });
                    }
                },
                items: {
                    "open": {name: "Open", icon: "fa-pencil"},
                    "preview": ((is_dynamic || !is_public) ? undefined : {name: "Preview", icon: "fa-eye"}),
                    "open_browser": ((is_dynamic || !is_public) ? undefined : {name: "Open in Browser", icon: "fa-globe"}),
                    "download": {name: "Download", icon: "fa-download"},
                    "sep1": "--------",
                    "set_exec": {name: (trigger.hasClass("exec") ? "Unset Executable" : "Set Executable"), icon: "fa-cog"},
                    "set_process": ((is_dynamic && !multiple_selected) ? {name: "Set Process", icon: "fa-cogs"} : undefined),
                    "sep2": "--------",
                    "rename": (multiple_selected ? undefined : {name: "Rename", icon: "fa-pencil-square-o"}),
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
                        trigger.dblclick();
                    }
                    if (key == "delete") {
                        triggerDelete();
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
                        trigger.dblclick();
                    }
                    if (key == "upload") {
                        uploader_folder = trigger;
                        $("#uploader").trigger("click");
                    }
                },
                items: {
                    "toggle": {name: "Toggle", icon: "fa-expand"},
                    "upload": {name: "Upload", icon: "fa-upload"},
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
    $.contextMenu({
        "selector": ".lm_tab",
        build: function(trigger, e) {
            var can_save = trigger.hasClass("tab-file") || trigger.hasClass("tab-nginx");
            var can_close = trigger.find(".lm_close_tab").length > 0;
            return {
                callback: function(key, options) {
                    if (key == "save") {
                        trigger.trigger("tab:save");
                    }
                    if (key == "close") {
                        trigger.find(".lm_close_tab").click();
                    }
                    if (key == "close_left") {
                        trigger.prevAll().each(function() {
                            var close = $(this).find(".lm_close_tab");
                            if (close.length) {
                                close.click();
                            }
                        });
                    }
                    if (key == "close_right") {
                        trigger.nextAll().each(function() {
                            var close = $(this).find(".lm_close_tab");
                            if (close.length) {
                                close.click();
                            }
                        });
                    }
                    if (key.startsWith("new_")) {
                        var newTab = {
                            type: "component",
                            componentName: key.substring(4)
                        };
                        trigger.trigger("tab:new", [newTab]);
                    }
                },
                items: {
                    "save": can_save ? {name: "Save", icon: "fa-save"} : undefined,
                    "sep1": can_save ? "--------" : undefined,
                    "close": can_close ? {name: "Close", icon: "fa-times-circle-o"} : undefined,
                    "close_left": {name: "Close Tabs to Left", icon: "fa-chevron-left"},
                    "close_right": {name: "Close Tabs to Right", icon: "fa-chevron-right"},
                    "sep2": "--------",
                    "new_terminal": {name: "New Terminal", icon: "fa-terminal"},
                    "new_nginx": {name: (is_superuser ? "Edit" : "View") + " Nginx Config", icon: "fa-pencil"},
                    "new_sql": typeof registerConsole == 'undefined' ? undefined : {name: "SQL Console", icon: "fa-database"},
                    "new_help": {name: "Settings", icon: "fa-wrench"}
                }
            };
        }
    });
    // end #files code
    function addContextHandlers(tab) {
        tab.element.on("tab:new", function(e, item) {
            tab.contentItem.parent.addChild(item);
        });
    }
    layout.registerComponent("files", function(container, componentState) {
        container.on("tab", addContextHandlers);
        container.setTitle("<span class='fa fa-folder-open'></span> Files");
        var files = $("<div id='files' tabindex='0' />");
        files.keydown(function(e) {
            var items = $("#files div.active");
            if (items.length > 0) {
                if (e.keyCode == 46) {
                    triggerDelete();
                    e.preventDefault();
                }
                if (e.keyCode == 13) {
                    items.dblclick();
                    e.preventDefault();
                }
                if (e.keyCode == 27) {
                    items.removeClass("active");
                    e.preventDefault();
                }
                if (e.keyCode == 82 && e.altKey) {
                    triggerRename(items.first());
                    e.preventDefault();
                }
                if (e.keyCode == 38) {
                    var na = items.prevAll(":visible");
                    if (na.length) {
                        items.removeClass("active");
                        na.first().addClass("active");
                    }
                    e.preventDefault();
                }
                if (e.keyCode == 40) {
                    var na = items.nextAll(":visible");
                    if (na.length) {
                        items.removeClass("active");
                        na.first().addClass("active");
                    }
                    e.preventDefault();
                }
            }
        });
        container.getElement().append(files);
        initFiles(true);
        registerFileHandlers(files);
    });
    layout.registerComponent("terminal", function(container, componentState) {
        container.on("tab", addContextHandlers);
        container.setTitle("<span class='fa fa-terminal'></span> Terminal");
        var term = $($("#console-wrapper-template").html());
        container.getElement().append(term);
        registerTerminal(term, terminal_auth, function(title) {
            container.setTitle("<span class='fa fa-terminal'></span> " + title);
        });
        container.on("resize", function() {
            term.trigger("terminal:resize");
        });
    });
    layout.registerComponent("preview", function(container, componentState) {
        container.on("tab", addContextHandlers);
        container.setTitle("<span class='fa fa-eye'></span> " + componentState.file);
        var frame = $("<iframe class='preview' />");
        frame.attr("sandbox", "allow-forms allow-pointer-lock allow-popups allow-scripts");
        var final_url = site_url + componentState.path.replace(/^public\//, "");
        frame.attr("src", final_url);
        container.getElement().append(frame);
    });
    layout.registerComponent("help", function(container, componentState) {
        container.on("tab", addContextHandlers);
        container.setTitle("<span class='fa fa-wrench'></span> Settings");
        container.getElement().html($("#settings-template").html());
        container.on("open", function() {
            updateSettings();
        });
    });
    layout.registerComponent("sql", function(container, componentState) {
        container.on("tab", addContextHandlers);
        if (typeof registerConsole !== 'undefined') {
            container.setTitle("<span class='fa fa-database'></span> SQL");
            container.getElement().html($("#sql-console-template").html());
            registerConsole(container.getElement().find(".sql-console"));
        }
        else {
            container.getElement().html("<b>No database provisioned!</b> Add a database in order to use the SQL console.");
        }
    });
    layout.registerComponent("nginx", function(container, componentState) {
        container.setTitle("<span class='file-indicator fa fa-wrench " + (is_superuser ? "saved" : "readonly") + "'></span> " + "Nginx");
        container.on("tab", addContextHandlers);
        var editor = ace.edit(container.getElement()[0]);
        editors.push(editor);
        editor.setOptions({
            "fontSize": settings["font-size"] + "px",
            "showPrintMargin": false,
            "theme": settings["editor-theme"]
        });
        container.on("close", function() {
            editors.splice(editors.indexOf(editor), 1);
        });
        container.on("resize", function() {
            editor.resize();
        });
        container.on("tab", function(tab) {
            tab.element.addClass("tab-nginx");
            tab.element.on("tab:save", function() {
                container.getElement().trigger("tab:save");
            });
        });
        container.getElement().on("tab:save", function(e, force) {
            if (!editor.getSession().getUndoManager().isClean()) {
                $.post(nginx_endpoint, { editor: editor.getSession().getValue(), force: (force ? true : undefined) }, function(data) {
                    if (data.error) {
                        if (data.force) {
                            var msg = Messenger().post({
                                message: data.error,
                                type: "error",
                                actions: {
                                    force: {
                                        label: "Force Save",
                                        action: function() {
                                            container.getElement().trigger("tab:save", [true]);
                                            msg.hide();
                                        }
                                    }
                                }
                            });
                        }
                        else {
                            Messenger().error(data.error);
                        }
                    }
                    else {
                        editor.getSession().getUndoManager().markClean();
                        container.tab.element.find("span.file-indicator").addClass("saved");
                        if (force) {
                            Messenger().success("Custom nginx configuration enabled!");
                        }
                    }
                });
            }
        });
        container.getElement().keydown(function(e) {
            if (((e.which == 115 || e.which == 83) && (e.ctrlKey || e.metaKey)) || e.which == 19) {
                $(this).trigger("tab:save");
                e.preventDefault();
                e.stopPropagation();
            }
        });
        $.get(nginx_endpoint, function(data) {
            var nginx_session = ace.createEditSession(data);
            nginx_session.setMode("ace/mode/space");
            nginx_session.on("change", function() {
                container.tab.element.find("span.file-indicator").removeClass("saved");
            });
            nginx_session.getUndoManager().markClean();
            editor.setSession(nginx_session);
        }, "text");
    });
    layout.registerComponent("file", function(container, componentState) {
        container.on("tab", addContextHandlers);
        if (componentState.isImage) {
            container.setTitle(componentState.file);
            var img = $("<img />");
            img.attr("src", download_endpoint + "?name=" + encodeURIComponent(componentState.path) + "&embed=true");
            var img_container = $("<div class='image-container' />");
            img_container.append(img);
            container.getElement().append(img_container);
        }
        else if (componentState.isMedia) {
            container.setTitle(componentState.file);
            var obj;
            if (componentState.path.toLowerCase().match(/\.pdf$/) != null) {
                obj = $("<embed class='embedded' type='application/pdf' />");
            }
            else {
                obj = $("<iframe class='embedded' />");
            }
            obj.attr("src", download_endpoint + "?name=" + encodeURIComponent(componentState.path) + "&embed=true");
            container.getElement().append(obj);
        }
        else {
            container.setTitle("<span class='file-indicator fa fa-circle-o saved'></span> " + componentState.file);
            var editor = ace.edit(container.getElement()[0]);
            editors.push(editor);
            editor.setOptions({
                "fontSize": settings["font-size"] + "px",
                "showPrintMargin": false,
                "enableBasicAutocompletion": true,
                "theme": settings["editor-theme"]
            });
            container.on("close", function() {
                editors.splice(editors.indexOf(editor), 1);
            });
            container.on("resize", function() {
                editor.resize();
            });
            container.on("tab", function(tab) {
                tab.element.addClass("tab-file");
                tab.element.on("tab:save", function() {
                    container.getElement().trigger("tab:save");
                });
            });
            container.getElement().on("tab:save", function(e, force) {
                if (!editor.getSession().getUndoManager().isClean()) {
                    $.post(save_endpoint + "?name=" + encodeURIComponent(componentState.path), { contents: editor.getSession().getValue(), force: (force ? true : undefined) }, function(data) {
                        if (data.error) {
                            if (data.force) {
                                var msg = Messenger().post({
                                    message: data.error,
                                    type: "error",
                                    actions: {
                                        force: {
                                            label: "Force Save",
                                            action: function() {
                                                container.getElement().trigger("tab:save", [true]);
                                                msg.hide();
                                            }
                                        }
                                    }
                                });
                            }
                            else {
                                Messenger().error(data.error);
                            }
                        }
                        else {
                            editor.getSession().getUndoManager().markClean();
                            container.tab.element.find("span.file-indicator").addClass("saved");

                            $.each(layout.root.getItemsById("preview-" + componentState.path), function(k, v) {
                                var frame = v.element.find("iframe");
                                frame.attr("src", frame.attr("src"));
                            });
                        }
                    });
                }
            });
            container.getElement().keydown(function(e) {
                if (((e.which == 115 || e.which == 83) && (e.ctrlKey || e.metaKey)) || e.which == 19) {
                    $(this).trigger("tab:save");
                    e.preventDefault();
                    e.stopPropagation();
                }
            });
            $.get(load_endpoint + "?name=" + encodeURIComponent(componentState.path), function(data) {
                if (data.error) {
                    Messenger().error(data.error);
                    container.close();
                }
                else {
                    var session = ace.createEditSession(data.contents);
                    session.setMode(modelist.getModeForPath(componentState.file).mode);
                    session.on("change", function() {
                        container.tab.element.find("span.file-indicator").removeClass("saved");
                    });
                    session.getUndoManager().markClean();
                    editor.setSession(session);
                }
            });
        }
    });
    $(window).resize(function() {
        layout.updateSize();
    });
    layout.init();

    $("#modal-confirm").on("shown.bs.modal", function() {
        var field = $("#modal-confirm .modal-prompt");
        if (field.length) {
            field.focus().select();
        }
        else {
            $("#modal-confirm .btn-primary").focus();
        }
    });
    $("#modal-confirm").on("hidden.bs.modal", function() {
        $("#files").focus();
    });

    addFileListener();
});
function join(a, b) {
    return [].slice.call(arguments).filter(function(path) { return !!path; }).map(function(path) {
        if (path[0] == "/") {
            path = path.slice(1);
        }
        if (path[path.length - 1] == "/") {
            path = path.slice(0, path.length - 1);
        }
        return path;
    }).join("/");
}
function addFileListener() {
    try {
        var host = location.origin.replace(/^http/, 'ws');
        var ws = new WebSocket(host + "/ws/");
        ws.onopen = function(e) {
            ws.send(JSON.stringify({ uid: terminal_auth.uid, token: terminal_auth.token, site: terminal_auth.site, editor: true }));
            ws.onmessage = function(e) {
                var data = JSON.parse(e.data);
                if (data.action == "create") {
                    if (!data.path) {
                        var newNode = makeNode({name: data.name, type: data.type ? "d" : "f", executable: data.exec, link: data.link}, 0);
                        if (!$("div." + (data.type ? "folder" : "file") + "[data-depth=0][data-name='" + data.name.replace("'", "\\'") + "']").length) {
                            $("#files").append(newNode);
                            if (data.type) {
                                newNode.trigger("dblclick");
                            }
                        }
                    }
                    else {
                        var node = getElement(data.path);
                        var newNode = makeNode({name: data.name, type: data.type ? "d" : "f", executable: data.exec, link: data.link}, parseInt(node.attr("data-depth")) + 1);
                        if (!node.nextUntil("div.folder[data-depth=" + node.attr("data-depth") + "]").filter("div." + (data.type ? "folder" : "file") + "[data-depth=" + (parseInt(node.attr("data-depth") + 1)) + "][data-name='" + data.name.replace("'", "\\'") + "']").length) {
                            node.after(newNode);
                            if (data.type) {
                                newNode.trigger("dblclick");
                            }
                        }
                    }
                }
                else if (data.action == "delete") {
                    var full_path = data.name;
                    if (data.path) {
                        full_path = join(data.path, data.name);
                    }
                    var del = getElement(full_path);
                    if (del) {
                        if (del.hasClass("folder")) {
                            getChildren(del).remove();
                        }
                        del.remove();
                    }
                }
            };
            $(document).on("folder:load", "#files div.folder", function() {
                ws.send(JSON.stringify({action: "listen", path: getPath($(this))}));
            });
        };
        ws.onclose = function() {
            $(document).off("folder:load", "#files div.folder");
            setTimeout(addFileListener, 1000);
        };
    }
    catch (e) {
        console.error(e);
    }
}
function getElement(path) {
    var p = path.split("/");
    var ele = $("#files").children("div.folder, div.file");
    var depth = 0;
    while (p.length) {
        var next = p.shift();
        ele = ele.filter("[data-depth=" + depth + "][data-name='" + next.replace("'", "\\'") + "']");
        if (!ele.length) {
            return false;
        }
        if (!p.length) {
            return ele;
        }
        ele = $(ele[0]).nextUntil("div.folder[data-depth=" + depth + "]");
        depth++;
    }
    return false;
}
function getPath(t) {
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
        return parseInt($(this).attr("data-depth")) <= depth;
    });
}
function getSiblings(item) {
    var depth = parseInt(item.attr("data-depth"));
    var before = item.prevUntil("[data-depth=" + (depth - 1) + "]").filter("[data-depth=" + depth + "]");
    var after = item.nextUntil("[data-depth=" + (depth - 1) + "]").filter("[data-depth=" + depth + "]");
    return before.add(after);
}
function modalConfirm(title, body, callback) {
    $("#modal-confirm").modal("show");
    $("#modal-confirm .modal-title").text(title);
    $("#modal-confirm .modal-body").html(body);
    $("#modal-confirm .btn-primary").off("click").on("click", callback);
}
function modalPrompt(title, body, callback, existing) {
    $("#modal-confirm").modal("show");
    $("#modal-confirm .modal-title").text(title);
    var bodytext = $("<p />");
    bodytext.text(body);
    $("#modal-confirm .modal-body").html(bodytext);
    $("#modal-confirm .modal-body").append("<input type='text' class='modal-prompt form-control' />");
    $("#modal-confirm .modal-prompt").off("keypress").on("keypress", function(e) {
        if (e.which == 13) {
            $("#modal-confirm .btn-primary").click();
            e.preventDefault();
        }
    }).val(existing || "");
    $("#modal-confirm .btn-primary").off("click").on("click", function() {
        var input = $("#modal-confirm .modal-prompt").val();
        if (input) {
            callback(input);
        }
    });
}
function makeNode(v, depth) {
    depth = depth || 0;
    var c = (v.type == "f" ? "file" : "folder");
    var ic = c;
    var node = $("<div draggable='true' style='padding-left:" + (depth * 20) + "px'><i class='fa fa-fw'></i> <span>" + $("<div />").text(v.name).html() + "</span></div>");
    node.addClass(c);
    node.attr("data-name", v.name);
    node.attr("data-depth", depth);
    if (v.executable) {
        node.addClass("exec");
    }
    if (v.link) {
        node.addClass("link");
    }
    if (v.name.charAt(0) == ".") {
        node.addClass("hidden");
    }
    if (v.type == "f") {
        var vnl = v.name.toLowerCase();
        if (vnl.match(/\.(jpeg|jpg|gif|png|ico)$/) != null) {
            node.addClass("image");
            ic = "file-image";
        }
        if (vnl.match(/\.(mp3|mp4|pdf|swf)$/) != null) {
            node.addClass("media");
            if (vnl.match(/\.pdf$/)) {
                ic = "file-pdf";
            }
            else {
                ic = "file-video";
            }
        }
        if (vnl.match(/\.(doc|docx|odt)$/) != null) {
            ic = "file-word";
        }
        if (vnl.match(/\.(py|php|js|html|css)$/) != null) {
            ic = "file-code";
        }
        if (vnl.match(/\.(txt|log)/) != null) {
            ic = "file-text";
        }
        if (vnl.match(/\.(zip|rar|gz|tar|7z|bz2|xz)$/) != null) {
            ic = "file-archive";
        }
    }
    node.find("i.fa").addClass("fa-" + ic + "-o");
    return node;
}

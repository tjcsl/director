$(document).ready(function() {
    var modelist = ace.require("ace/ext/modelist");
    ace.require("ace/ext/language_tools");
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
            content:[{
                type: 'component',
                componentName: 'files',
                width: 25,
                isClosable: false
            },{
                type: 'column',
                content:[{
                    type: 'stack',
                    isClosable: false,
                    id: "default-file"
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

    layout.on("stateChanged", function() {
        if (typeof localStorage !== 'undefined') {
            var state = JSON.stringify(layout.toConfig());
            localStorage.setItem("editor-state-" + site_name, state);
        }
    });

    // #files code
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
        if (item[0] == $("#files")[0]) {
            filepath = "";
        }
        else {
            var filepath = get_path(item);
        }
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
    function makeNode(v, depth) {
        depth = depth || 0;
        var c = (v.type == "f" ? "file" : "folder");
        var ic = c;
        var node = $("<div draggable='true' style='padding-left:" + (depth*20) + "px'><i class='fa fa-fw'></i> <span>" + $("<div />").text(v.name).html() + "</span></div>");
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
                    var node = makeNode(v);
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
    function registerFileHandlers(files) {
        files.on("click", ".file", function(e) {
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
        files.on("click", ".folder", function(e) {
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
                            var node = makeNode(v, depth + 1);
                            if (!getChildren(t).filter("div[data-depth=" + (depth + 1) + "][data-name='" + v.name.replace("'", "\\'") + "']").length) {
                                t.after(node);
                            }
                        });
                        t.find(".fa-fw").removeClass("fa-folder-o").addClass("fa-folder-open-o");
                    }
                });
            }
        });
        var path_obj;
        files.on("dragstart", "div", function(e) {
            var item = $(this);
            var filepath = get_path(item);
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
                                    if (f.hasClass("folder") && !f.find(".fa-fw").hasClass("fa-folder-open-o")) {
                                        f.click();
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
    }
    var uploader_folder = null;
    $("#uploader").on("change", function(e) {
        if (!this.files.length) {
            return;
        }
        var formData = new FormData();
        if (uploader_folder) {
            formData.append("path", get_path(uploader_folder));
        }
        else {
            formData.append("path", "");
        }
        for (var i = 0; i < this.files.length; i++) {
            formData.append("file[]", this.files[i], this.files[i].name);
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
                    if (uploader_folder) {
                        uploader_folder.removeClass("loaded");
                        uploader_folder.click();
                    }
                    else {
                        initFiles();
                    }
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
                    if (key == "upload") {
                        uploader_folder = null;
                        $("#uploader").trigger("click");
                    }
                },
                items: {
                    "open": {name: "Open Website", icon: "fa-globe"},
                    "sep1": "--------",
                    "upload": {name: "Upload", icon: "fa-upload"},
                    "new_file": {name: "New File", icon: "fa-file"},
                    "new_folder": {name: "New Folder", icon: "fa-folder"},
                    "sep2": "--------",
                    "new_terminal": {name: "New Terminal", icon: "fa-terminal"},
                    "new_nginx": {name: "Edit Nginx Config", icon: "fa-wrench"},
                    "new_sql": typeof registerConsole == 'undefined' ? undefined : {name: "SQL Console", icon: "fa-database"},
                    "sep3": "--------",
                    "refresh": {name: "Refresh", icon: "fa-refresh"}
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
                        $("#files div.file.active").click();
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
                    if (key == "preview") {
                        var filepath = get_path(trigger) + trigger.attr("data-name");
                        if (filepath.startsWith("public/")) {
                            var newTab = {
                                id: "preview-" + filepath,
                                type: "component",
                                componentName: "preview",
                                componentState: { path: filepath, file: trigger.attr("data-name") }
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
                            Messenger().error("This file cannot be previewed.");
                        }
                    }
                },
                items: {
                    "open": {name: "Open", icon: "fa-pencil"},
                    "preview": {name: "Preview", icon: "fa-eye"},
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
    // end #files code

    layout.registerComponent("files", function(container, componentState) {
        container.setTitle("Files");
        var files = $("<div id='files' />");
        container.getElement().append(files);
        initFiles(true);
        registerFileHandlers(files);
    });
    layout.registerComponent("terminal", function(container, componentState) {
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
        container.setTitle("<span class='fa fa-eye'></span> " + componentState.file);
        var frame = $("<iframe class='preview' />");
        frame.attr("sandbox", "allow-forms allow-pointer-lock allow-popups allow-scripts");
        var final_url = site_url + componentState.path.replace(/^public\//, "");
        frame.attr("src", final_url);
        container.getElement().append(frame);
    });
    layout.registerComponent("sql", function(container, componentState) {
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
        container.setTitle("<span class='file-indicator fa fa-wrench saved'></span> " + "Nginx");
        var editor = ace.edit(container.getElement()[0]);
        editor.setOptions({
            "fontSize": "12pt",
            "showPrintMargin": false
        });
        container.on("resize", function() {
            editor.resize();
        });
        container.getElement().keydown(function(e) {
            if (((e.which == 115 || e.which == 83) && e.ctrlKey) || e.which == 19) {
                if (!editor.getSession().getUndoManager().isClean()) {
                    $.post(nginx_endpoint, { editor: editor.getSession().getValue() }, function(data) {
                        if (data.error) {
                            Messenger().error(data.error);
                        }
                        else {
                            editor.getSession().getUndoManager().markClean();
                            container.tab.element.find("span.file-indicator").addClass("saved");
                        }
                    });
                }
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
            editor.setOptions({
                "fontSize": "12pt",
                "showPrintMargin": false,
                "enableBasicAutocompletion": true
            });
            container.on("resize", function() {
                editor.resize();
            });
            container.getElement().keydown(function(e) {
                if (((e.which == 115 || e.which == 83) && e.ctrlKey) || e.which == 19) {
                    if (!editor.getSession().getUndoManager().isClean()) {
                        $.post(save_endpoint + "?name=" + encodeURIComponent(componentState.path), { contents: editor.getSession().getValue() }, function(data) {
                            if (data.error) {
                                Messenger().error(data.error);
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
        return parseInt($(this).attr("data-depth")) <= depth;
    });
}

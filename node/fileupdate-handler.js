var path = require("path");
var fs = require("fs");
var Inotify = require("inotify").Inotify;
var inotify = new Inotify();

var onlineUsers = {};

module.exports = {
    onlineUsers: onlineUsers,
    register: function(ws, data) {
        function sendUserCount() {
            var msg = JSON.stringify({
                action: "users",
                users: onlineUsers[data.site.name].sockets.map(function(x) { return x.user; })
            });
            for (var i = 0; i < onlineUsers[data.site.name].sockets.length; i++) {
                var s = onlineUsers[data.site.name].sockets[i];
                if (s.readyState == 1) {
                    // websocket is in OPEN state
                    s.send(msg);
                }
            }
        }
        function addHook(p) {
            if (!path.join(data.site.homedir, p).startsWith(data.site.homedir)) {
                return;
            }
            if (!onlineUsers[data.site.name] || p in onlineUsers[data.site.name].hooks) {
                return;
            }
            onlineUsers[data.site.name].hooks[p] = inotify.addWatch({
                path: path.join(data.site.homedir, p),
                watch_for: Inotify.IN_CREATE | Inotify.IN_DELETE | Inotify.IN_MOVED_FROM | Inotify.IN_MOVED_TO | Inotify.IN_IGNORED | Inotify.IN_DELETE_SELF | Inotify.IN_MODIFY,
                callback: function(e) {
                    var act = null;
                    var stat = null;
                    if (e.mask & (Inotify.IN_DELETE_SELF | Inotify.IN_IGNORED)) {
                        delete onlineUsers[data.site.name].hooks[p];
                        return;
                    }
                    if (e.mask & (Inotify.IN_DELETE | Inotify.IN_MOVED_FROM)) {
                        act = "delete";
                    }
                    if (e.mask & Inotify.IN_MODIFY) {
                        act = "modify";
                    }
                    if (e.mask & (Inotify.IN_CREATE | Inotify.IN_MOVED_TO)) {
                        act = "create";
                    }
                    if (act == "create" || act == "modify") {
                        try {
                            stat = fs.lstatSync(path.join(data.site.homedir, p, e.name));
                        }
                        catch (err) {
                            if (err && err.code == "ENOENT") {
                                return;
                            }
                        }
                    }
                    if (act) {
                        var msg = JSON.stringify({
                            path: (p ? p : undefined),
                            type: !!(e.mask & Inotify.IN_ISDIR),
                            name: e.name,
                            action: act,
                            exec: (stat ? ((stat.mode & 1) && !stat.isDirectory()) : undefined),
                            link: (stat ? stat.isSymbolicLink() : undefined)
                        });
                        for (var i = 0; i < onlineUsers[data.site.name].sockets.length; i++) {
                            var s = onlineUsers[data.site.name].sockets[i];
                            if (s.readyState == 1) {
                                // websocket is in OPEN state
                                s.send(msg);
                            }
                        }
                    }
                }
            });
        }
        if (data.site.name in onlineUsers) {
            onlineUsers[data.site.name].sockets.push(ws);
        }
        else {
            onlineUsers[data.site.name] = {sockets: [ws], hooks: {}};
        }
        addHook("");
        addHook("public");
        ws.on("close", function() {
            onlineUsers[data.site.name].sockets.splice(onlineUsers[data.site.name].sockets.indexOf(ws), 1);
            if (!onlineUsers[data.site.name].sockets) {
                for (var hook in onlineUsers[data.site.name].hooks) {
                    try {
                        inotify.removeWatch(onlineUsers[data.site.name].hooks[hook]);
                    }
                    catch (e) {
                        // watch was already removed
                    }
                }
                delete onlineUsers[data.site.name];
            }
            else {
                sendUserCount();
            }
        });
        // remove any dead connections
        for (var i = onlineUsers[data.site.name].sockets.length - 1; i >= 0; i--) {
            if (onlineUsers[data.site.name].sockets[i].readyState == 3) {
                onlineUsers[data.site.name].sockets.splice(i, 1);
            }
        }
        sendUserCount();
        ws.on("message", function(d) {
            var data = JSON.parse(d);
            if (data.action == "listen") {
                addHook(data.path);
            }
        });
    }
};

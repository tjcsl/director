var path = require("path");
var fs = require("fs");
var Inotify = require("inotify").Inotify;
var inotify = new Inotify();

var onlineUsers = {};

module.exports = {
    onlineUsers: onlineUsers,
    register: function(ws, auth, data) {
        function sendUserCount() {
            var msg = JSON.stringify({
                action: "users",
                users: onlineUsers[auth.site_name].sockets.map(function(x) { return x.user; })
            });
            for (var i = 0; i < onlineUsers[auth.site_name].sockets.length; i++) {
                var s = onlineUsers[auth.site_name].sockets[i];
                if (s.readyState == 1) {
                    // websocket is in OPEN state
                    s.send(msg);
                }
            }
        }
        function addHook(p) {
            if (!path.join(auth.site_homedir, p).startsWith(auth.site_homedir)) {
                return;
            }
            if (!onlineUsers[auth.site_name] || p in onlineUsers[auth.site_name].hooks) {
                return;
            }
            onlineUsers[auth.site_name].hooks[p] = inotify.addWatch({
                path: path.join(auth.site_homedir, p),
                watch_for: Inotify.IN_CREATE | Inotify.IN_DELETE | Inotify.IN_MOVED_FROM | Inotify.IN_MOVED_TO | Inotify.IN_IGNORED | Inotify.IN_DELETE_SELF | Inotify.IN_MODIFY,
                callback: function(e) {
                    var act = null;
                    var stat = null;
                    if (e.mask & (Inotify.IN_DELETE_SELF | Inotify.IN_IGNORED)) {
                        delete onlineUsers[auth.site_name].hooks[p];
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
                            stat = fs.lstatSync(path.join(auth.site_homedir, p, e.name));
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
                        for (var i = 0; i < onlineUsers[auth.site_name].sockets.length; i++) {
                            var s = onlineUsers[auth.site_name].sockets[i];
                            if (s.readyState == 1) {
                                // websocket is in OPEN state
                                s.send(msg);
                            }
                        }
                    }
                }
            });
        }
        if (auth.site_name in onlineUsers) {
            onlineUsers[auth.site_name].sockets.push(ws);
        }
        else {
            onlineUsers[auth.site_name] = {sockets: [ws], hooks: {}};
        }
        addHook("");
        addHook("public");
        ws.on("close", function() {
            onlineUsers[auth.site_name].sockets.splice(onlineUsers[auth.site_name].sockets.indexOf(ws), 1);
            if (!onlineUsers[auth.site_name].sockets) {
                for (var hook in onlineUsers[auth.site_name].hooks) {
                    try {
                        inotify.removeWatch(hooks[hook]);
                    }
                    catch (e) {
                        // watch was already removed
                    }
                }
                delete onlineUsers[auth.site_name];
            }
            else {
                sendUserCount();
            }
        });
        // remove any dead connections
        for (var i = onlineUsers[auth.site_name].sockets.length - 1; i >= 0; i--) {
            if (onlineUsers[auth.site_name].sockets[i].readyState == 3) {
                onlineUsers[auth.site_name].sockets.splice(i, 1);
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

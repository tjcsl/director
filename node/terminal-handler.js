var pty = require("pty.js");
var uuid = require("uuid/v4");

var terminals = {};

module.exports = {
    terminals: terminals,
    resizeTerminal: function(id, rows, cols) {
        if (typeof terminals[id] !== "undefined") {
            return false;
        }
        terminals[id].resize(rows, cols);
        return true;
    },
    register: function(ws, auth, data) {
        var id = uuid();
        var started = false;
        var term = null;
        ws.on("close", function() {
            if (term) {
                term.destroy();
            }
            delete terminals[id];
        });

        if (data.site) {
            if (!auth.user) {
                ws.send(JSON.stringify({ error: "Invalid user id passed!" }));
                ws.close();
            }
            else {
                term = pty.spawn(__dirname + "/shell.sh", [auth.user], {
                    name: "xterm-color",
                    cols: 80,
                    rows: 30,
                    cwd: auth.site_homedir,
                    env: {
                        SITE_ROOT: auth.site_homedir,
                        SITE_NAME: auth.site_name,
                        SITE_PURPOSE: auth.site_purpose
                    }
                });
            }
        }
        else if (data.vm) {
            term = pty.spawn(__dirname + "/ssh.sh", [auth.ip], {
                name: "xterm-color",
                cols: 80,
                rows: 30,
                env: {
                    SSHPASS: auth.password
                }
            });
        }

        term.on("close", function(e) {
            ws.close();
            delete terminals[id];
        });
        term.on("data", function(data) {
            ws.send(data);
        });
        ws.on("message", function(data) {
            term.write(data);
        });
        terminals[id] = term;
        started = true;
        if (ws.readyState == 1) {
            ws.send(JSON.stringify({ id: id, action: "START" }));
        }
    }
};

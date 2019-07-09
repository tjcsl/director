var pty = require("pty.js");
var uuid = require("uuid/v4");

var terminals = {};

module.exports = {
    terminals: terminals,
    resizeTerminal: function(id, rows, cols) {
        if (typeof terminals[id] === "undefined") {
            return false;
        }
        terminals[id].resize(rows, cols);
        return true;
    },
    register: function(ws, data) {
        var id = uuid();
        // var started = false;
        var term = null;
        ws.on("close", function() {
            if (term) {
                term.destroy();
            }
            delete terminals[id];
        });

        if (data.site) {
            if (!data.user) {
                ws.send(JSON.stringify({ error: "Invalid user id passed!" }));
                ws.close();
            }
            else {
                var args = [data.user];
                if (data.custom && data.custom.command) {
                    args = [data.site.user, data.custom.command];
                }
                term = pty.spawn(__dirname + "/shell.sh", args, {
                    name: "xterm-color",
                    cols: 80,
                    rows: 30,
                    cwd: data.site.homedir,
                    env: {
                        SITE_ROOT: data.site.homedir,
                        SITE_NAME: data.site.name,
                        SITE_PURPOSE: data.site.purpose,
                        SITE_URL: data.site.url,
                        LANG: "en-US.UTF-8",
                        LC_ALL: "en-US.UTF-8",
                        LC_CTYPE: "en-US.UTF-8"
                    }
                });
            }
        }
        else if (data.vm) {
            term = pty.spawn(__dirname + "/ssh.sh", [data.vm.ip], {
                name: "xterm-color",
                cols: 80,
                rows: 30,
                env: {
                    SSHPASS: data.vm.password
                }
            });
        }
        else {
            ws.send(JSON.stringify({ error: "Unknown terminal type!" }));
            ws.close();
        }

        term.on("close", function() {
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
        // started = true;
        if (ws.readyState == 1) {
            ws.send(JSON.stringify({ id: id, action: "START" }));
        }
    }
};

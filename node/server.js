#!/usr/bin/node

var fs = require("fs");
var pty = require("pty.js");
var WebSocketServer = require('ws').Server;
var express = require("express");
var app = express();
var http = require("http");
var https = require("https");
var querystring = require("querystring");

var raven = require("raven");
if (fs.existsSync("raven.dsn")) {
    raven.config(fs.readFileSync("raven.dsn", "utf8")).install();
}

var uuid = require("uuid/v4");

var terminals = {};

app.set("port", (process.env.PORT || 8301));
app.use("/ws", express.static(__dirname + "/public"));

var server = require("http").createServer(app);
server.listen(app.get("port"));

app.post("/ws/terminal/:id/size", function(req, res) {
    res.setHeader("Content-Type", "application/json");
    var id = req.params.id;
    if (typeof terminals[id] !== "undefined") {
        var rows = parseInt(req.query.rows);
        var cols = parseInt(req.query.cols);
        terminals[id].resize(cols, rows);
        res.send(JSON.stringify({ success: true }));
    }
    else {
        res.send(JSON.stringify({ success: false }));
    }
    res.end();
});

var wss = new WebSocketServer({ server: server });
wss.on("connection", function(ws) {
    var id = uuid();
    var started = false;
    var term = null;
    ws.on("close", function() {
        if (term) {
            term.destroy();
        }
        delete terminals[id];
    });
    var message_init = function(data, flags) {
        data = JSON.parse(data);
        var postData = querystring.stringify({
            uid: data.uid,
            sid: data.site,
            vmid: data.vm,
            access_token: data.token
        });
        var req = http.request({
            method: "POST",
            hostname: "localhost",
            port: 601,
            path: "/wsauth",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "Content-Length": postData.length
            }
        }, function(resp) {
            resp.setEncoding("utf8");
            resp.on("data", function(authinfo) {
                try {
                    var auth = JSON.parse(authinfo);
                }
                catch (err) {
                    raven.captureException(err);
                    ws.send(JSON.stringify({ error: "Failed to parse auth server response!" }));
                    ws.close();
                    return;
                }
                if (!auth.granted) {
                    if (auth.exception) {
                        raven.captureMessage(auth.exception);
                    }
                    ws.send(JSON.stringify({ error: auth.error }));
                    ws.close();
                }
                else {
                    if (data.site !== null) {
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
                                    HOME: auth.site_homedir
                                }
                            });
                        }
                    }
                    else if (data.vm !== null) {
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
                    ws.removeListener("message", message_init);
                    ws.on("message", function(data) {
                        term.write(data);
                    });
                    terminals[id] = term;
                    started = true;
                    if (ws.readyState == 1) {
                        ws.send(JSON.stringify({ id: id, action: "START" }));
                    }
                }
            });
        });
        req.write(postData);
        req.end();
    };
    ws.on("message", message_init);
});


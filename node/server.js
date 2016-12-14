var pty = require("pty.js");
var WebSocketServer = require('ws').Server;
var express = require("express");
var app = express();
var http = require("http");
var https = require("https");

var uuid = require("uuid/v4");

var terminals = {};

app.set("port", (process.env.PORT || 8301));
app.use(express.static(__dirname + "/public"));

var server = require("http").createServer(app);
server.listen(app.get("port"));

app.get("/terminal", function(req, res) {
    res.sendFile(__dirname + "/public/terminal.html");
});

app.post("/terminal/:id/size", function(req, res) {
    var id = req.params.id;
    if (terminals[id]) {
        var rows = parseInt(req.query.rows);
        var cols = parseInt(req.query.cols);
        terminals[id].resize(cols, rows);
    }
    res.end();
});

var wss = new WebSocketServer({ server: server });
wss.on("connection", function(ws) {
    var id = uuid();
    var started = false;
    var term;
    terminals[id] = term;
    ws.on("close", function() {
        if (term) {
            term.destroy();
        }
        delete terminals[id];
    });
    ws.on("message", function(data, flags) {
        if (!started) {
            data = JSON.parse(data);
            https.post({ method: "POST", hostname: "director.tjhsst.edu", port: 443, path: "/nodeauth" }, { json: { uid: data.uid, sid: data.site, access_token: data.token } }, function(resp) {
                resp.setEncoding("utf8");
                resp.on("data", function(authinfo) {
                    var auth = JSON.parse(authinfo);
                    if (auth.error) {
                        ws.send(JSON.stringify({ action: "ERROR" }));
                    }
                    else {
                        term = pty.spawn(__dirname + "/run.sh", [auth.site_user], {
                            name: "xterm-color",
                            cols: 80,
                            rows: 30,
                            cwd: auth.site_homedir
                        });
                        term.on("close", function(e) {
                            ws.close();
                            delete terminals[id];
                        });
                        term.on("data", function(data) {
                            ws.send(data);
                        });
                        started = true;
                        ws.send(JSON.stringify({ id: id, action: "START" }));
                    }
                });
            });
        }
        else {
            term.write(data);
        }
    });
});


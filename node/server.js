#!/usr/bin/node

var fs = require("fs");
var WebSocketServer = require('ws').Server;
var express = require("express");
var app = express();
var http = require("http");
var https = require("https");
var querystring = require("querystring");

var handler_fileupdate = require("./fileupdate-handler.js");
var handler_terminal = require("./terminal-handler.js");
var handler_log = require("./log-handler.js");

var raven = require("raven");
if (fs.existsSync("raven.dsn")) {
    raven.config(fs.readFileSync("raven.dsn", "utf8")).install();
}

app.set("port", (process.env.PORT || 8301));

var server = require("http").createServer(app);
server.listen(app.get("port"), function() {
    console.log("Server started on port " + app.get("port") + "...");
});

app.post("/ws/terminal/:id/size", function(req, res) {
    res.setHeader("Content-Type", "application/json");
    var id = req.params.id;
    var rows = parseInt(req.query.rows);
    var cols = parseInt(req.query.cols);
    res.send(JSON.stringify({ success: handler_terminal.resizeTerminal(id, cols, rows) }));
    res.end();
});

var wss = new WebSocketServer({ server: server });
wss.on("connection", function(ws) {
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
                var auth;
                try {
                    auth = JSON.parse(authinfo);
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
                    ws.user = auth.user;
                    ws.removeListener("message", message_init);
                    if ("custom" in data) {
                        auth.custom = data.custom;
                    }
                    if (data.type == "fileupdate") {
                        handler_fileupdate.register(ws, auth);
                    }
                    else if (data.type == "log") {
                        handler_log.register(ws, auth);
                    }
                    else if (data.type == "terminal") {
                        handler_terminal.register(ws, auth);
                    }
                    else {
                        ws.send(JSON.stringify({ error: "Unknown request type!" }));
                        ws.close();
                    }
                }
            });
        });
        req.write(postData);
        req.end();
    };
    ws.on("message", message_init);
});


#!/usr/bin/node

var pty = require("pty.js");
var WebSocketServer = require('ws').Server;
var express = require("express");
var app = express();
var http = require("http");
var https = require("https");
var querystring = require("querystring");

var uuid = require("uuid/v4");

var terminals = {};

app.set("port", (process.env.PORT || 8301));
app.use("/ws", express.static(__dirname + "/public"));

var server = require("http").createServer(app);
server.listen(app.get("port"));

app.get("/ws/terminal", function(req, res) {
    res.sendFile(__dirname + "/public/terminal.html");
});

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
    ws.on("close", function() {
        if (term) {
            term.destroy();
        }
        delete terminals[id];
    });
    ws.on("message", function(data, flags) {
        if (!started) {
            data = JSON.parse(data);
            var postData = querystring.stringify({
                uid: data.uid,
                sid: data.site,
                access_token: data.token
            });
            var req = https.request({
                method: "POST",
                hostname: "director.tjhsst.edu",
                port: 443,
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
                        console.error(err);
                        console.log(authinfo);
                        ws.send(JSON.stringify({ action: "ERROR", message: "Failed to parse auth server response!" }));
                        ws.close();
                        return;
                    }
                    if (!auth.granted) {
                        if (auth.exception) {
                            console.error(auth.exception);
                        }
                        ws.send(JSON.stringify({ action: "ERROR", message: auth.error }));
                        ws.close();
                    }
                    else {
                        var term = pty.spawn(__dirname + "/run.sh", [auth.site_user], {
                            name: "xterm-color",
                            cols: 80,
                            rows: 30,
                            cwd: auth.site_homedir,
                            env: { HOME: auth.site_homedir }
                        });
                        term.on("close", function(e) {
                            ws.close();
                            delete terminals[id];
                        });
                        term.on("data", function(data) {
                            ws.send(data);
                        });
                        terminals[id] = term;
                        started = true;
                        ws.send(JSON.stringify({ id: id, action: "START" }));
                    }
                });
            });
            req.write(postData);
            req.end();
        }
        else {
            term.write(data);
        }
    });
});


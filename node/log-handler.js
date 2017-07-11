var fs = require("fs");
var fst = require("fs-tail-stream");
var path = require("path");

module.exports = {
    register: function(ws, data) {
        ws.send(JSON.stringify({ action: "START" }));
        var filename;
        if ("custom" in data && data.custom.path) {
            filename = path.normalize(path.join(data.site.homedir, data.custom.path));
            if (!filename.startsWith(data.site.homedir)) {
                ws.send("Invalid log file at " + filename + ".");
                ws.close();
                return;
            }
        }
        else {
            filename = path.join(data.site.homedir, "private", "log-" + data.site.name + ".log");
        }
        fs.stat(filename, function (err) {
            if (err && err.code == "ENOENT") {
                ws.send("No log file at " + filename + ".");
                ws.close();
            } else {
                var stream = fst.createReadStream(filename, { encoding: "utf8", tail: true });
                stream.on("error", function () {
                    if (ws.readyState == 1) {
                        ws.send("An error occurred while reading the log.");
                    }
                });
                stream.on("data", function (data) {
                    if (ws.readyState == 1) {
                        ws.send(data);
                    }
                });
                ws.on("close", function() {
                    stream.close();
                });
            }
        });
    },
};

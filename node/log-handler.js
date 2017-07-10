var fs = require("fs");
var fst = require("fs-tail-stream");
var path = require("path");

module.exports = {
    register: function(ws, data) {
        var filename = path.join(data.site.homedir, "private", `log-${data.site.name}.log`);
        fs.stat(filename, function (err, stats) {
            if (err && err.code == "ENOENT") {
                ws.send(JSON.stringify({
                    text: `No log file at ${filename}`,
                    error: "No log file"}));
                ws.close();
            } else {
                var stream = fst.createReadStream(filename, { encoding: "utf8", tail: true });
                stream.on("error", function () {
                    ws.send(JSON.stringify({error: "An error occurred reading the log."}));
                });
                stream.on("data", function (data) {
                    ws.send(JSON.stringify({text: data}));
                });
                ws.on("close", function() {
                    stream.close();
                });
            }
        })
    },
};

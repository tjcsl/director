$(document).ready(function() {
    if (!window.WebSocket) {
        $("#console").text('No WebSocket support!');
    }
    else {
        main();
    }
    $(document).keypress(function(e) {
        if (e.which == 13 && restart) {
            main();
        }
    });
});
var restart = false;
function main() {
    restart = false;
    var started = false;
    var host = location.origin.replace(/^http/, 'ws');
    var ws = new WebSocket(host + "/ws/");
    var termid;
    ws.onopen = function(e) {
        $("#console").empty();
        var term = new Terminal({ cursorBlink: true });
        term.on("data", function(data) {
            if (started) {
                ws.send(data);
            }
        });
        term.on("resize", function(size) {
            if (!termid) {
                return;
            }
            $.post("/ws/terminal/" + encodeURIComponent(termid) + "/size?cols=" + size.cols + "&rows=" + size.rows);
        });
        term.on("title", function(title) {
            document.title = title;
        });
        ws.send(JSON.stringify({ uid: gup("uid"), token: gup("token"), site: window.location.hash.substring(1) }));
        ws.onmessage = function(e) {
            if (started) {
                term.write(e.data);
            }
            else {
                var data = JSON.parse(e.data);
                if (data.error) {
                    console.error(data.error);
                }
                if (data.id) {
                    termid = data.id;
                    term.open(document.getElementById("console"));
                    term.fit();
                }
                if (data.action == "START") {
                    started = true;
                }
            }
        };
        ws.onclose = function(e) {
            var cache = $("#console").html();
            term.destroy();
            $(window).unbind("resize");
            $("#console").html(cache);
            $($("#console .terminal div").get().reverse()).each(function(i, v) {
                if ($(v).text().trim().length == 0) {
                    $(v).remove();
                }
                else {
                    return false;
                }
            });
            started = false;
            document.title = 'Terminal';
            $("#console .terminal .xterm-rows").append('<div>&nbsp;</div><b style="color:red">Connection lost, press ENTER to reconnect</b></div>');
            restart = true;
        };
        $(window).resize(function(e) {
            if (started) {
                term.fit();
            }
        });
    };
}
function gup(name, url) {
    if (!url) url = location.href;
    name = name.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
    var regexS = "[\\?&]"+name+"=([^&#]*)";
    var regex = new RegExp( regexS );
    var results = regex.exec( url );
    return results == null ? null : results[1];
}

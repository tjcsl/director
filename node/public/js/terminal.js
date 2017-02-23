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
        $("#console").empty().removeClass("disconnected");
        $("#disconnect").hide();
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
        ws.send(JSON.stringify({ uid: gup("uid"), token: gup("token"), site: gup("site"), vm: gup("vm") }));
        ws.onmessage = function(e) {
            if (started) {
                term.write(e.data);
            }
            else {
                var data = JSON.parse(e.data);
                if (data.error) {
                    $("#console").append("<div style='color:red'>Error: " + $("<div />").text(data.error).html() + "</div>");
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
            try {
                term.destroy();
            }
            catch (ignore) {  }
            $(window).unbind("resize");
            $("#console").html(cache).addClass("disconnected");
            started = false;
            document.title = 'Terminal';
            $("#disconnect").show();
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

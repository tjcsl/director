$(document).ready(function() {
    $(window).resize(function() {
        $(".console-wrapper").trigger("terminal:resize");
    });
});
function registerTerminal(wrapper, auth, titlecallback) {
    titlecallback = titlecallback || function(title) {
        document.title = title;
    };
    var console = wrapper.find(".console");
    var disconnect = wrapper.find(".disconnect");
    var started = false;
    var host = location.origin.replace(/^http/, 'ws');
    var ws = new WebSocket(host + "/ws/");
    var termid;
    ws.onopen = function(e) {
        console.empty().removeClass("disconnected");
        disconnect.hide();
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
            titlecallback(title);
        });
        ws.send(JSON.stringify(auth));
        ws.onmessage = function(e) {
            if (started) {
                term.write(e.data);
            }
            else {
                var data = JSON.parse(e.data);
                if (data.error) {
                    console.append("<div style='color:red'>Error: " + $("<div />").text(data.error).html() + "</div>");
                }
                if (data.id) {
                    termid = data.id;
                    term.open(console[0]);
                    term.fit();
                }
                if (data.action == "START") {
                    started = true;
                }
            }
        };
        ws.onclose = function(e) {
            var cache = console.html();
            try {
                term.destroy();
            }
            catch (ignore) { }
            wrapper.off("resize");
            console.html(cache).addClass("disconnected");
            started = false;
            wrapper.focus();
            disconnect.show();
            titlecallback("Terminal");
        };
        wrapper.keypress(function(e) {
            if (e.which == 13) {
                wrapper.off("keypress");
                wrapper.off("resize");
                registerTerminal(wrapper, auth, titlecallback);
            }
        });
        wrapper.on("terminal:resize", function(e) {
            e.preventDefault();
            e.stopPropagation();
            if (started) {
                term.fit();
            }
        });
    };
}
function gup(name, url) {
    if (!url) url = location.href;
    name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
    var regexS = "[\\?&]" + name + "=([^&#]*)";
    var regex = new RegExp(regexS);
    var results = regex.exec(url);
    return results == null ? null : results[1];
}

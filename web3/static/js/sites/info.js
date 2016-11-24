$(document).ready(function() {
    $("#git-pull").click(function() {
        $.get(git_pull_endpoint, function(data) {
            $("#git-output").text("Process exited with return code " + data.ret + (data.out ? "\n\n" + data.out : "") + (data.err ? "\n\n" + data.err : "")).slideDown("fast");
        });
    });
    $("#generate-key").click(function(e) {
        if ($(this).text().indexOf("Regenerate") > -1) {
            if (!confirm("Are you sure you want to regenerate keys for this site?")) {
                e.preventDefault();
            }
        }
    });
});
var select = function(el) {
    var range = document.createRange();
    range.selectNodeContents(el);
    var sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
}
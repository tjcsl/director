/* global
        ace
*/
$(document).ready(function () {
    $("select[name='author']").selectize();
    $("select[name='tag']").selectize({
        create: true
    });
    var md = window.markdownit({
        html: true,
        linkify: true,
        typographer: true
    });

    var editor = ace.edit("editor");
    var textarea = $("textarea[name='content']");
    var output = $(".output");

    editor.getSession().setUseWrapMode(true);
    editor.getSession().setMode("ace/mode/markdown");
    editor.getSession().on("change", function () {
        textarea.val(editor.getSession().getValue());
        output.html(md.render(editor.getSession().getValue()));
    });
});

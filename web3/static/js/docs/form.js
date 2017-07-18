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

    editor.setFontSize(16);
    editor.getSession().setUseWrapMode(true);
    editor.getSession().setMode("ace/mode/markdown");
    editor.getSession().on("change", function () {
        textarea.val(editor.getSession().getValue());
        output.html(md.render(editor.getSession().getValue()));
    });

    function onResize() {
        $(".raw").height($(window).height() - $(".raw").position().top);
        $(".output").height($(window).height() - $(".output").position().top - 30);
    }
    $(window).resize(onResize);
    onResize();
});

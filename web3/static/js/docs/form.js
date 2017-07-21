/* global
        ace
        hljs
*/
$(document).ready(function () {
    $("select[name='author']").selectize();
    var md = window.markdownit({
        html: true,
        linkify: true,
        typographer: true,
        highlight: function (str, lang) {
            if (lang && hljs.getLanguage(lang)) {
                try {
                    return hljs.highlight(lang, str).value;
                } catch (e) {
                    // Do nothing
                }
            }
            return ""; // use external default escaping
        }
    });

    var editor = ace.edit("editor");
    var textarea = $("textarea[name='content']");
    var output = $(".output");

    if (textarea.val() !== "") {
        editor.setValue(textarea.val());
        editor.clearSelection();
        output.html(md.render(editor.getSession().getValue()));
    }

    editor.setFontSize(16);
    editor.renderer.setShowGutter(false);
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

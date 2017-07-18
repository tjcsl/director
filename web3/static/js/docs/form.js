/* global
        ace
*/
$(document).ready(function () {
    $("select[name='author']").selectize();
    $("select[name='tags']").selectize({
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
    //
    // if (textarea.val() !== "") {
    //     editor.getSession.setValue(textarea.val());
    // }

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

    $("button").click(function (e) {
        e.preventDefault();
        if ($(this).text() === "post") {
            document.querySelector("#id_published").checked = true;
        }
    });
});

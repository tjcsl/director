/* global
    hljs
*/
hljs.initHighlightingOnLoad();
$(document).ready(function() {
    $(".guide h4, .guide h5, .guide h6").each(function() {
        var title = $(this).text();
        var link = title.toLowerCase().replace(/ /g, "-");
        $(this).attr("name", link);
        var item = $("<a />").text(title);
        item.attr("href", "#" + link);
        item.addClass("level");
        item.addClass("level-" + $(this).prop("tagName").toLowerCase());
        $(".toc").append(item);
    });
    $(".toc h5").click(function() {
        $("html, body").animate({
            scrollTop: 0
        }, 400);
    });
    $(".toc .level").click(function() {
        var loc = $(".guide [name='" + $(this).attr("href").substring(1) + "']");
        $("html, body").animate({
            scrollTop: loc.offset().top
        }, 400);
    });
    if (window.location.hash) {
        $("html, body").scrollTop($(".guide [name='" + window.location.hash.substring(1) + "']").offset.top);
    }
});

/* global
        Cookies

        revision_endpoint
        publish_endpoint
        unpublish_endpoint
        */

var revisions = {};

$(function () {
    $("a.article").click(function () {
        var id = $(this).data("rid");
        var published = $(this).data("published");
        if (revisions[id]) {
            display(revisions[id], id, published);
        } else {
            $.get(`${revision_endpoint.slice(0, -1)}${$(this).data("rid")}?text`, function (data) {
                revisions[id] = data;
                display(data, id, published);
            });
        }
    });

    $(".output").on("click", "a.publish", function () {
        var action = $(this).data("action");
        var rid = $(this).data("revision_id");
        if (action == "publish") {
            $.post(publish_endpoint,
                {
                    revision_id: rid,
                    csrfmiddlewaretoken: Cookies.get("csrftoken")
                }, function (data) {
                    if (data.success) {
                        Messenger().success("Successfully published article! :)");
                        rerender(rid, "publish");
                    }
                    else if (data.error) {
                        Messenger().error(data.error);
                    }
                });
        } else if (action == "unpublish") {
            $.post(unpublish_endpoint,
                {
                    revision_id: rid,
                    csrfmiddlewaretoken: Cookies.get("csrftoken")
                }, function (data) {
                    if (data.success) {
                        Messenger().success("Successfully unpublished article!");
                        rerender(rid, "unpublish");
                    }
                    else if (data.error) {
                        Messenger().error(data.error);
                    }
                });
        } else {
            Messenger().error("Unsupported action!");
        }
    });
});

function display(data, rid, published) {
    var output = $(".output");
    output.html($(".preview-template").html());
    output.find(".preview-sticky .sticky-text").text(`Previewing Revision ID #${rid}`);
    output.find(".preview-sticky .publish")
        .text(`${(published) ? "Unpublish" : "Publish this Version"}`)
        .data("action", `${(published) ? "unpublish" : "publish"}`)
        .data("revision_id", rid);
    output.find(".preview-sticky .preview")
        .text("Preview")
        .attr("href",`${revision_endpoint.slice(0, -1)}${rid}`);
    output.find(".preview-title").text(data.title);
    output.find(".preview-output").html(data.html);
}

function rerender (rid, action) {
    $("[data-published=true]")
        .data("published", false)
        .find("span.tag").remove();
    if (action == "publish") {
        $(`[data-rid=${rid}]`)
            .data("published", true)
            .attr("data-published", true)
            .find("b").append($(".public-tag-template").html());
    }
}

if(typeof is_admin == 'undefined') is_admin = false;
$(function() {
    roster_endpoint = $('body').attr('data-roster-endpoint');
    if(roster_endpoint) roster_endpoint = roster_endpoint.substring(0, roster_endpoint.length-1);

    activity_endpoint = $('body').attr('data-activity-endpoint');
    if(activity_endpoint) activity_endpoint = activity_endpoint.substring(0, activity_endpoint.length-1);

    window.selectize = [];

    data = {};

    getActivityData = function(act, callback) {
        act = parseInt(act);
        console.log("actData", act);
        if(act in data) {
            callback(data[act]);
            return
        }
        $.get(activity_endpoint + act, {}, function(d) {
            r = JSON.parse(d);
            data[act] = r;
            callback(data[act]);
        }, "text");
    }

    blockChange = function(bid) {
        console.log("blockChange", bid)
        var elm = $("select[data-block=" + bid + "]");
        var s = elm[0].selectize;
        var val = parseInt(s.getValue());
        
        getActivityData(val, function(actdata) {
            showDetail(bid, actdata);
        });
    }

    showDetail = function(bid, act) {
        console.log("showDetail", bid, act);
        if(!act) {
            detail.html("").attr("data-activity", null);
            return;
        }
        var detail = $(".block-detail[data-block=" + bid + "]");
        var html = "<div class='act-name'><b>Activity</b>: " + act.name.split('\n').join('<br/>') + "</div>" + 
                   "<b>Category:</b> " + act.category + "<br />" +
                   "<b>Room:</b> " + act['room-name'] + "<br />" +
                   "<b>Description:</b> " + act.description + "<br />";
        if(act.presenters) {
            html+= "<b>Presenters:</b> " + act.presenters + "<br />";
        }

        if(act.projects.length > 0) {
            html += "<br />";
            for(var i=0; i<act.projects.length; i++) {
                var p = act.projects[i];
                html += p;
                html += "<br />";
            }
        }

        html += "<div style='margin-top: 5px'><b>";
        if(is_admin) {
            html += "<a href='" + roster_endpoint + "" + act.activity + "'>";
        }
        html += act.signups + " of " + act.capacity + " people";
        if(is_admin) html += "</a>";
        html += "</b> have signed up for this activity.<br /></div>";
        detail.html(html);
        detail.attr("data-activity", act.activity);
    }

    var blksSel = [];
    $("select").each(function() {
        var bid = $(this).attr("data-block");
        bid = parseInt(bid);

        $("option[data-activity]", $(this)).each(function() {
            var aid = parseInt($(this).attr("data-activity"));
            if($(this).attr("data-was-selected")) blksSel.push(bid);
            // $(this).attr("data-data", JSON.stringify({"title": $(this).html(), "value": $(this).val()}));
        });

        selRender = function(item, escape) {
            console.log(item);
            var text = item.text;
            text = text.split("\n").join("<br/>");
            text = text.replace('[b]', "<b>");
            text = text.replace('[/b]', "</b>");
            text = text.replace('[SELECTED]', '<span class="badge green">Selected</span>');
            text = text.replace('[RESTRICTED]', '<span class="badge purple">Restricted</span>');
            text = text.replace('[STICKY]', '<span class="badge orange">Sticky</span>');
            return '<div>' + text + '</div>';
        }

        var s = $(this).selectize({
            onChange: new Function("blockChange("+bid+")"),
            render: {
                option: selRender,
                item: selRender
            }
        });


        s = s[0].selectize;
        window.selectize.push(s);
    });

    for(var i=0; i<blksSel.length; i++) {
        blockChange(blksSel[i]);
    }
});
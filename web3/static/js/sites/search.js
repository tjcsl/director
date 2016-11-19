$(document).ready(function() {
    $('#select-site').selectize({
        valueField: 'url',
        labelField: 'name',
        searchField: 'name',
        create: false,
        render: {
            option: function(item, escape) {
                return '<div>' +
                '<span class="title">' +
                '<span class="name"><i class="fa ' + (item.purpose == 'user' ? 'fa-user' : 'fa-globe') + '"></i> ' + escape(item.name) + '</span>' +
                '</span>' +
                '<span class="description">' + escape(item.description) + '</span>' +
                '<ul class="meta">' +
                (item.category ? '<li class="language">' + escape(item.category) + '</li>' : '') +
                '<li class="watchers"><span>' + escape(item.users) + '</span> users</li>' +
                '</ul>' +
                '</div>';
            }
        },
        score: function(search) {
            var score = this.getScoreFunction(search);
            return function(item) {
                return score(item) * (1 + Math.min(item.users / 100, 1));
            };
        },
        load: function(query, callback) {
            if (!query.length) return callback();
            $.ajax({
                url: "/site/all",
                type: 'GET',
                error: function() {
                    callback();
                },
                success: function(res) {
                    callback(res.sites);
                }
            });
        }
    });
    $("#select-site").change(function(){
        window.location.href = $("#select-site").val()
    });
});
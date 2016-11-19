$(document).ready(function() {
    $.ajax({
            url: "/site/all",
            type: 'GET',
            error: function() {
                site_list = []
            },
            success: function(res) {
                site_list = res.sites
            },
            async: false
    });
    $("#select-site").on('input', function(){
        val = $(this).val()
        for(var i = 0; i < site_list.length; i++){
            obj = site_list[i];
            if(obj.name.includes(val) || obj.description.includes(val)){
                console.log(obj);
                $("#"+site_list[i].name).show();
            }
            else{
                $("#"+site_list[i].name).hide();
            }
        }
    });
});
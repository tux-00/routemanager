$(function() {
    $(':checkbox[id]').change(function() {
        var id = this.id;
        if ($(this).is(':checked')) {
            $.ajax({
                type: 'POST',
                url: '/change_client_status',
                data: {
                    cid: id,
                    cnewstatus: 1
                },
                beforeSend: function(jqXHR, settings) {
                    $(':checkbox[id]').prop('disabled', true);
                },
                success: function(response) {
                    if (response.status == 'error') {
                        console.log(response);
                        // Route isn't activated -> reset checkbox state
                        $('#'+id).prop('checked', false);
                        //$("#tr-"+id).removeClass("active")
                    }
                    if (response.status == 'exist') {
                        console.log('exist ' + id);
                        // Route isn't activated -> reset checkbox state
                        $('#'+id).prop('checked', false);
                    }
                    $(':checkbox[id]').prop('disabled', false);
                },
                error: function(error) {
                    $(':checkbox[id]').prop('disabled', false);
                }
            });
        } else {
            $.ajax({
                type: 'POST',
                url: '/change_client_status',
                data: {
                    cid: id,
                    cnewstatus: 0
                },
                beforeSend: function(jqXHR, settings) {
                    $(':checkbox[id]').prop('disabled', true);
                },
                success: function(response) {
                    if (response.status == 'error') {
                        console.log('error');
                    }
                    $(':checkbox[id]').prop('disabled', false);
                },
                error: function(error) {
                    $(':checkbox[id]').prop('disabled', false);
                }
            });
        }
    })
});

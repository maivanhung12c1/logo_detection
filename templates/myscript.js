function change_by_uuid(){
    var input = document.getElementsByName("image_uuid")[0].value
    document.getElementById("uuid_form").action = "/" + input
}
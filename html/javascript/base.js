var host = "http://" + window.location.host + "/rest/1/"

document.onkeydown = checkKey;

function checkKey(e) {
    e = e || window.event;
    e = e.keyCode

    if (e == 27) {
        $(".loginsignup-frame").hide()
    }
}

function format() {
    var s = arguments[0];
    for (var i = 0; i < arguments.length - 1; i++) {       
        var reg = new RegExp("\\{" + i + "\\}", "gm");             
        s = s.replace(reg, arguments[i + 1]);
    }
    return s;
}

function storeCookie(cname, value) {
    f = "{0}={1}; path=/"
    document.cookie = format(f, cname, value);
}

function getCookie(cname) {
    var name = cname + "=";
    var ca = document.cookie.split(';');
    for(var i=0; i<ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1);
        if (c.indexOf(name) == 0) return c.substring(name.length,c.length);
    }
    return "";
}

function deleteCookie (cname) {
    document.cookie = cname + "=; path=/";
}

function selectfile (e) {
    accept = e.accept.split(",")
    filename = e.files[0]["name"]

    $("#" + e.id + "-filename")[0].innerText = ""
    breaked = false;
    $.each(accept, function (_, i) {
        if (filename.endsWith(i)) {
            $("#" + e.id + "-filename")[0].innerText = filename;
            breaked = true;
            return false;
        } 
    })
    if (!breaked) {
        alert("檔案格式不合")
    }
}

function checkfile (eid) {
    if ($("#" + eid + "-filename")[0].textContent != "") {
        return true;
    }
    else {
        return false;
    }
}
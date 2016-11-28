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

function deleteCookie(cname) {
	document.cookie = cname + "=; path=/";
}
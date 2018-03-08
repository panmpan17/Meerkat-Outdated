var host = "http://" + window.location.host + "/rest/1/"

document.onkeydown = checkKey;

function checkKey(e) {
    e = e || window.event;
    e = e.keyCode

    if (e == 27) {
        hide_allpopup();
    }
}

console.log("add format function to string")
String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) { 
      return typeof args[number] != 'undefined'
        ? args[number]
        : match
      ;
    });
};

function format() {
    var s = arguments[0];
    for (var i = 0; i < arguments.length - 1; i++) {       
        var reg = new RegExp("\\{" + i + "\\}", "gm");             
        s = s.replace(reg, arguments[i + 1]);
    }
    return s;
}

console.log("add equals function to array")
Array.prototype.equals = function (array) {
    // if the other array is a falsy value, return
    if (!array)
        return false;

    // compare lengths - can save a lot of time 
    if (this.length != array.length)
        return false;

    for (var i = 0, l=this.length; i < l; i++) {
        // Check if we have nested arrays
        if (this[i] instanceof Array && array[i] instanceof Array) {
            // recurse into the nested arrays
            if (!this[i].equals(array[i]))
                return false;       
        }           
        else if (this[i] != array[i]) { 
            // Warning - two different object instances will never be equal: {x:20} != {x:20}
            return false;   
        }           
    }       
    return true;
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
    if ($("#" + eid)[0].value != "") {
        return true;
    }
    else {
        return false;
    }
}
document.onkeydown = checkKey;
window_ = ["signup-frame", "login-frame", "opinion-frame", "ask-frame", "question-frame"]

function checkKey(e) {
    e = e || window.event;
    e = e.keyCode

    if (e == 27) {
        for (var i = window_.length - 1; i >= 0; i--) {
            try {
                hide(window_[i])
            }
            catch(err) {}
        }
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
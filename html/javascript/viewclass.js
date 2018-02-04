card_format = `
<div class="col-md-6 col-sm-12">
    <div class="classview-container" onclick="goclass('{0}')">
        <div class="classview-card">
            <center>
                <div class="col-sm-4 col-xs-12">
                    <img src="/html/images/class/{0}.png" class="card-image" />
                </div>
                <div class="col-sm-8 col-xs-12">
                        <div id="{0}-title" class="title">
                            {1}
                            <span id="time">{2}</span>
                        </div>
                        <div class="describe">
                            {3}
                        </div>
                        <span id="price">
                            {4}
                        </span>
                </div>
            </center>
        </div>
    </div>
</div>`

describe_format = `
<div hidden id="{0}-frame" class="loginsignup-frame">
    <div class="loginsignup-frame-inside">
        <a id="closeloginframe" onclick="hide('{0}-frame');" style="">X</a>
        <br>
        <center>
            <a onclick="leadtoclass('{0}');hide('{0}-frame')">
                <button id="goclass">前往課程</button>
            </a>
        </center>
        <hr>
        <div class="frame-content"
            style="padding:15px;padding-top: 0%;padding-bottom: 50px;">
            {1}
        </div>
    </div>
</div>`

classess_info = {}

function goclass(id) {
    a = $("#" + id + "-frame")[0];
    if (a != undefined) {
        show(id + "-frame")
    }
    else {
        leadtoclass(id)
    }
}

function leadtoclass(id) {
    u_key = getCookie("key")

    class_ = classess_info[id]
    json = {"class": id, "key": u_key}
    if (getCookie("teacher-key") != "") {
        json["tkey"] = getCookie("teacher-key")
    }
    $.ajax({
        url: host + "classroom/student_permission",
        type: "GET",
        data: json,
        success: function (msg) {
            if (msg["success"]) {
                if (msg["key"] == "teacher") {
                    storeCookie("clsrid", msg["permission"][0]["id"])
                    window.location.href = "/class/c/" + id;
                }
                else {
                    if (msg["class"].length == 1) {
                        storeCookie("clsrid", msg["class"][0]["id"]);
                        window.location.href = "/class/c/" + id;
                        return
                    }
                    html = ""
                    $.each(msg["class"], function (_, i) {
                        html += format(`<div class="class" onclick="chose_classroome({0}, '{2}')">{1}</div>`,
                            i["id"],
                            i["name"],
                            id,
                            )
                    })

                    $("#classroom-confirm #list")[0].innerHTML = html
                    show("blackscreen");
                    show("classroom-confirm");
                }
            }
            else if (class_["trial"].length > 0) {
                if (class_["permission"] == null) {
                    $("#alert #title")[0].innerHTML = format(`您還沒有登入`)
                    $("#alert #describe")[0].innerHTML = format(
                        "要試試 {0} 堂的體驗課程<br>還是要登入觀看完整課程",
                        class_["trial"].length
                        )
                    $("#alert #btns")[0].innerHTML = format(`
                        <button class="mybtn primary" onclick="window.location.href = '/class/c/{0}'">看體驗課程</button>
                        <button class="mybtn primary" onclick="dismiss_alert();show('login-frame')">登入</button>
                        <button class="mybtn" onclick="dismiss_alert()">都不用謝謝</button>`,
                        id
                        )
                    $(".loginsignup-frame").hide()
                    $("#blackscreen").show()
                    $("#alert").show()
                    return
                }

                if (msg["reason"] == "not in class") {
                    $("#alert #title")[0].innerHTML = format(`您不是 "{0}" 的學員，無法進入`,
                        class_["subject"])
                }
                else if (msg["reason"] == "no permission") {
                    $("#alert #title")[0].innerHTML = format(`您的教師帳號沒有 {0} 的權限，無法進入`,
                        class_["subject"])
                }

                $("#alert #describe")[0].innerHTML = format(
                    "有 {0} 個體驗課程<br>是否要試試",
                    class_["trial"].length
                    )
                $("#alert #btns")[0].innerHTML = format(`
                    <button class="mybtn primary" onclick="window.location.href = '/class/c/{0}'">好, 看體驗課程</button>
                    <button class="mybtn" onclick="dismiss_alert()">不用謝謝</button>`,
                    id
                    )
                $("#blackscreen").show()
                $("#alert").show()
            }
            else {
                $("#alert #title")[0].innerHTML = format(`您不是 "{0}" 的學員，無法進入`,
                    class_["subject"])
                $("#alert #describe")[0].innerHTML = "無體驗課程"
                $("#alert #btns")[0].innerHTML = format(`
                    <button class="mybtn" onclick="dismiss_alert()">知道了</button>`,
                    )
                $("#blackscreen").show()
                $("#alert").show()
            }
        },
        error: function (error) {
            if (class_["permission"] == null) {
                $("#alert #title")[0].innerHTML = format(`您還沒有登入`)
                $("#alert #describe")[0].innerHTML = format(
                    "要試試 {0} 堂的體驗課程<br>還是要登入觀看完整課程",
                    class_["trial"].length
                    )
                $("#alert #btns")[0].innerHTML = format(`
                    <button class="mybtn primary" onclick="window.location.href = '/class/c/{0}'">看體驗課程</button>
                    <button class="mybtn primary" onclick="dismiss_alert();show('login-frame')">登入</button>
                    <button class="mybtn" onclick="dismiss_alert()">都不用謝謝</button>`,
                    id
                    )
                $(".loginsignup-frame").hide()
                $("#blackscreen").show()
                $("#alert").show()
                return
            }
            else {
                if (error.status == 401) {
                    $("#alert #title")[0].innerHTML = format(`您還沒有登入`,
                        class_["subject"])
                    $("#alert #describe")[0].innerHTML = ""
                    $("#alert #btns")[0].innerHTML = format(`
                        <button class="mybtn primary" onclick="dismiss_alert();show('login-frame')">登入</button>
                        <button class="mybtn" onclick="dismiss_alert()">不用謝謝</button>`,
                        id
                        )
                    $("#blackscreen").show()
                    $("#alert").show()
                    return null;
                }
            }
        }
    })
}

function chose_classroome (clsid, id) {
    storeCookie("clsrid", clsid)
    window.location.href = "/class/c/" + id;
}

$.ajax({
    url: host + "classes/",
    type: "GET",
    success: function (msg) {
        cardstext = "";
        $.each(msg, function (_, i) {
            if (i["id"] == "teacher_1") {
                return true;
            }

            classess_info[i["id"]] = i

            if (i["permission"] == null) {
                price = "免費線上課程"
            }
            else if (i["permission"] == "class") {
                price = "需要配合實體課程，不開放線上課程"
            }
            else if (i["permission"] == "login") {
                price = "免費線上課程，需註冊並登入"
            }
            else if (i["permission"] == "online") {
                price = "線上課程"
            }
            cardstext += format(card_format,
                i["id"],
                i["subject"],
                i["time"],
                i["summary"],
                price)

            if (i["description"] != "") {
                $("#describes")[0].innerHTML += format(describe_format,
                    i["id"],
                    i["description"])
            }

            setTimeout(function () {
                if (i["style"]["title_color"] != undefined) {
                    $("#" + i["id"] + "-title")[0].style.color = i["style"]["title_color"]
                }
            }, 100)
        })
        $("#cards")[0].innerHTML = cardstext
    }
})

function dismiss_alert () {
    $("#blackscreen").hide()
    $("#alert").hide()
}
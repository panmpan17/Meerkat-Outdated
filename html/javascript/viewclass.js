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
            <a onclick="leadtoclass('{0}')">
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
    class_ = classess_info[id]
    if (class_["permission"] != null) {
        json = {"class": id, "key": getCookie("key")}
        if (getCookie("teacher-key") != "") {
            json["tkey"] = getCookie("teacher-key")
        }
        $.ajax({
            url: host + "classroom/student_permission",
            type: "GET",
            data: json,
            success: function (msg) {
                console.log(msg)
                if (msg.length == 1 || getCookie("teacher-key") != "") {
                    storeCookie("clsrid", msg[0]["id"])
                    window.location.href = "/class/c/" + id;
                }

                console.log(msg)
                
                $.each(msg, function (_, i) {
                    $("#classroom-confirm #list")[0].innerHTML += format(`<div class="class" onclick="chose_classroome({0}, '{2}')">{1}</div>`,
                        i["id"],
                        i["name"],
                        id,
                        )
                })

                show("blackscreen");
                show("classroom-confirm");
            },
            error: function (error) {
                if (error.status == 401) {
                    reload = confirm("請登錄");
                    if (reload) {
                        show("login-frame");
                    }
                    return null;
                }
                else if (error.status == 400) {
                    alert("您不是 Python 學員，無法進入")
                }
            }
        })
    }
    else {
        window.location.href = "/class/c/" + id
    }
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
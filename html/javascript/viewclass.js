card_format = `
<div class="col-md-6 col-sm-12">
    <div class="classview-container" onclick="goclass('{0}')">
        <div class="classview-card">
            <center>
                <div class="col-sm-4 col-xs-12">
                    <img src="/html/images/class/{0}.png" class="card-image" />
                </div>
                <div class="col-sm-8 col-xs-12">
                        <div class="title">
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
            <a onclick="leadtoclass('{0}', {2})">
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

function goclass(id) {
    a = $("#" + id + "-frame")[0];
    if (a != undefined) {
        show(id + "-frame")
    }
    else {
        leadtoclass(id)
    }
}

function leadtoclass(id, price) {
    if (price != 0) {
        json = {"class": id, "key": getCookie("key")}
        $.ajax({
            url: host + "classroom/student_permission",
            type: "GET",
            data: json,
            success: function (msg) {
                window.location.href = "/class/c/" + id;
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

$.ajax({
    url: host + "classes/",
    type: "GET",
    success: function (msg) {
        cardstext = "";
        for (i=0;i<msg.length;i++) {
            if (msg[i]["id"] == "teacher_1") {
                continue
            }

            price = "NT " + msg[i]["price"]
            if (msg[i]["price"] == 0) {
                price = "免費"
            }
            else if (msg[i]["price"] == -1) {
                price = "只提供實體課程"
            }
            else if (msg[i]["price"] == -2) {
                price = "免費線上課程"
            }
            cardstext += format(card_format,
                msg[i]["id"],
                msg[i]["subject"],
                msg[i]["time"],
                msg[i]["summary"],
                price)

            if (msg[i]["description"] != "") {
                $("#describes")[0].innerHTML += format(describe_format,
                    msg[i]["id"],
                    msg[i]["description"],
                    msg[i]["price"])
            }
        }
        $("#cards")[0].innerHTML = cardstext
    }
})
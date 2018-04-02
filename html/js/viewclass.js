unic_images = [
    "unic-1.png",
    "unic-2.png",
    "unic-3.png",
    "unic-4.png",
    "unic-5.png",
]

card_format = `<button class="card">
    <img src="{3}" >
    <br>
    <div class="title">{0}</div>
    <div class="description">
        {1}
    </div>
    <div class="btn-group">
        <div class="full-btn" onclick="to_class('{2}')">進入完整課程</div>
    </div>
</button>`

direct_card_format = `<button class="card">
    <img src="{3}" >
    <br>
    <div class="title">{0}</div>
    <div class="description">
        {1}
    </div>
    <div class="btn-group">
        <div class="full-btn" onclick="window.location.href='/class/c/{2}'">進入完整課程</div>
    </div>
</button>`

card_noaccess_format = `<button class="card">
    <img src="{3}" >
    <br>
    <div class="title">{0}</div>
    <div class="description">
        {1}
    </div>
    <div class="btn-group">
        <div onclick="start_trial('{2}')" class="trial-btn">體驗課程</div><!-- 
        --><div onclick="apply_class('{2}')" class="apply-btn">報名課程</div>
    </div>
</button>`

card_notrial_format = `<button class="card">
    <img src="{3}" >
    <br>
    <div class="title">{0}</div>
    <div class="description">
        {1}
    </div>
    <div class="btn-group">
        <div onclick="start_trial('{2}')" class="trial-btn">體驗課程</div><!-- 
        --><div onclick="apply_class('{2}')" class="apply-btn">報名課程</div>
    </div>
</button>`

card_noaccess_notrial_format = `<button class="card">
    <img src="{3}" >
    <br>
    <div class="title">{0}</div>
    <div class="description">
        {1}
    </div>
    <div class="btn-group">
        <div onclick="apply_class('{2}')" class="full-btn">報名課程</div>
    </div>
</button>`

classess_info = {}
classroom_in = null
login_as = null

function goclass(id) {
    a = $("#" + id + "-frame")[0];
    if (a != undefined) {
        show(id + "-frame")
    }
    else {
        leadtoclass(id)
    }
}

function chose_classroome (clsid, id) {
    storeCookie("clsrid", clsid)
    window.location.href = "/class/c/" + id;
}

function start_trial (cls_type) {
    if (classess_info[cls_type]["permission"] == null) {
        $("#alert #title")[0].innerHTML = format(`您還沒有登入`)
        $("#alert #describe")[0].innerHTML = format(
            "要試試 {0} 堂的體驗課程<br>還是要登入觀看完整課程",
            classess_info[cls_type]["trial"].length
            )

        $("#alert #btns")[0].innerHTML = format(
            `<button class="btn btn-orange" onclick="hide_popup('alert');show_popup('login-frame')">馬上登入</button>
            <button class="btn btn-default" onclick="window.location.href='/class/c/{0}'">不用登入，直接體驗課程</button>`,
            cls_type
            )

        show_popup("alert");
        return;
    }

    if (login_as != null) {
        window.location.href = "/class/c/" + cls_type;
    }
    else {
        $("#alert #title")[0].innerHTML = format(`您還沒有登入`)
        $("#alert #describe")[0].innerHTML = "要先登入才能體驗課程"

        $("#alert #btns")[0].innerHTML = `<button class="btn btn-orange" onclick="hide_popup('alert');show_popup('login-frame')">馬上登入</button>
            <button class="btn btn-default" onclick="hide_allpopup()">不用</button>`

        show_popup("alert");
    }
}

function to_class (cls_type) {
    if (available_class[cls_type] == "teacher") {
        window.location.href = "/class/c/" + cls_type;
    }
    else {
        storeCookie("clsrid", Object.keys(available_class[cls_type])[0]);
        window.location.href = "/class/c/" + cls_type;
    }
}

function apply_class (cls_type) {
    window.location.href = "/teacher/advertise"
}

$.ajax({
    url: host + "classes/all",
    type: "GET",
    data: {"key": getCookie("key"), "tkey": getCookie("teacher-key")},
    success: function (msg) {
        cardstext = "";

        if (msg["login"]) {
            available_class = msg["available_class"]

            var unic_index = 0;
            $.each(msg["info"], function (_, i) {
                classess_info[i["id"]] = i
                unic_index++;

                if (available_class[i["id"]] != undefined) {
                    cardstext += format(card_format,
                        i["subject"],
                        i["summary"],
                        i["id"],
                        "/html/images/unic/" + unic_images[unic_index],
                        )
                }
                else {
                    if (i["trial"].length == 0) {
                        cardstext += format(card_noaccess_notrial_format,
                            i["subject"],
                            i["summary"],
                            i["id"],
                            "/html/images/unic/" + unic_images[unic_index],
                            )
                    }
                    else {
                        if (i["permission"] == null) {
                            cardstext += format(direct_card_format,
                                i["subject"],
                                i["summary"],
                                i["id"],
                                "/html/images/unic/" + unic_images[unic_index],
                                )
                        }
                        else {
                            cardstext += format(card_noaccess_format,
                                i["subject"],
                                i["summary"],
                                i["id"],
                                "/html/images/unic/" + unic_images[unic_index],
                                )
                        }
                    }
                }
            })
            // else {
            //     var unic_index = 0;
            //     $.each(msg["info"], function (_, i) {
            //         unic_index++;
            //         classess_info[i["id"]] = i

            //         if (classroom_in.indexOf(i["id"]) != -1) {
            //             cardstext += format(card_format,
            //                 i["subject"],
            //                 i["summary"],
            //                 i["id"],
            //                 "/html/images/unic/" + unic_images[unic_index],
            //                 )
            //         }
            //         else {
            //             if (i["trial"].length == 0) {
            //                 cardstext += format(card_noaccess_notrial_format,
            //                     i["subject"],
            //                     i["summary"],
            //                     i["id"],
            //                     "/html/images/unic/" + unic_images[unic_index],
            //                     )
            //             }
            //             else {
            //                 cardstext += format(card_noaccess_format,
            //                     i["subject"],
            //                     i["summary"],
            //                     i["id"],
            //                     "/html/images/unic/" + unic_images[unic_index],
            //                     )
            //             }
            //         }
            //     })
            // }
        } 
        else {
            // no user or teacher login
            var unic_index = 0;
            $.each(msg["info"], function (_, i) {
                classess_info[i["id"]] = i

                if (i["trial"].length != 0) {
                    if (i["permission"] == null) {
                        cardstext += format(card_noaccess_format,
                            i["subject"],
                            i["summary"],
                            i["id"],
                            "/html/images/unic/" + unic_images[unic_index],
                            )
                    }
                    else {
                        cardstext += format(card_notrial_format,
                            i["subject"],
                            i["summary"],
                            i["id"],
                            "/html/images/unic/" + unic_images[unic_index],
                            )
                    }
                }
                else {
                    cardstext += format(card_noaccess_notrial_format,
                        i["subject"],
                        i["summary"],
                        i["id"],
                        "/html/images/unic/" + unic_images[unic_index],
                        )
                }

                unic_index ++
            })

            if (getCookie("key") == "" || getCookie("teacher-key") == "") {
                storeCookie("key", "");
                storeCookie("userid", "");
                storeCookie("id", "");
                storeCookie("teacher-key", "");
                storeCookie("teacher-id", "");
                storeCookie("teacher-userid", "");
                $(".non-login-menu").show();
                $(".login-menu").hide();
            }
        }

        $("#cards")[0].innerHTML = cardstext
    }
})
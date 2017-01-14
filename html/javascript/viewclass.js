card_format = `
<div class="col-md-6 col-sm-12">
  <div class="classview-container" onclick="goclass('{0}')">
    <div class="classview-card">
      <center>
        <div class="col-sm-4 col-xs-12">
          <img src="/html/images/{1}" class="card-image" />
        </div>
        <div class="col-sm-8 col-xs-12">
            <div class="title">
              {2}
              <span id="time">{3}</span>
            </div>
            <div class="describe">
              {4}
            </div>
            <span id="price">
              {5}
            </span>
        </div>
      </center>
    </div>
  </div>
</div>`

describe_format = `
<div id="{0}-frame" class="loginsignup-frame">
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
  a = document.getElementById(id + "-frame");
  if (a != undefined) {
    show(id + "-frame")
  }
  else {
    leadtoclass(id)
  }
}

function leadtoclass(id, price) {
  if (price != 0) {
    $.ajax({
      url: host + "classes/",
      type: "GET",
      data: {"class": id, "key": getCookie("key")},
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
          alert("你目前沒有權限")
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
      cardstext += format(card_format, msg[i]["id"], msg[i]["image"],
        msg[i]["subject"], msg[i]["time"], msg[i]["summary"], price)

      if (msg[i]["description"] != "") {
        document.getElementById("describes").innerHTML += format(describe_format,
          msg[i]["id"], msg[i]["description"], msg[i]["price"])
      }
    }
    document.getElementById("cards").innerHTML = cardstext
  }
})
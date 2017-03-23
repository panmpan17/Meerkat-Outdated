document.onkeydown = changeclass;

function changeclass(e) {
    e = e || window.event;
    e = e.keyCode

    if (e == 37) {
        prev();
    }
    if (e == 39) {
        next();
    }
}

var class_ = null;

var lesson = 0
var video = 0

var classblock = `<div class="class_block"\
 style="width:{0}%" onclick="video_jump({3})">{1}<div id="answer" style="display: {4}"></div></div>`;

var videoblock = `<div class=\"embed-responsive embed-responsive-16by9\">
<iframe id="videoframe" src=\"{0}&amp;showinfo=0\" frameborder=\"0\" allowfullscreen></iframe>
</div>`

var privatevideoblock = `<div class=\"embed-responsive embed-responsive-16by9\">
<iframe id="videoframe" src='http://{0}/video/{1}?video={2}&nextvid={3}'></iframe>
</div>`

var buttonblock = `<a target=\"_blank\" href=\"{1}\">
<button class=\"btn btn-primary\">{0}</button></a>`

var lessonblock = `<li><a onclick="loadclass(subject_id, {0})">{1}</a></li>`

var questionblock = `<br /><br />
<div style="text-align: left;">
<a onclick="video_jump({0})"><button class="btn btn-primary">問題</button></a>
</div>
`

function loadclass(classname, qlesson=-1) {
	j = {"class":classname}
	key = getCookie("key")
	if (key != "") {
		j["key"] = key
	}

	if (class_ != null && qlesson == -1) { return; }
	if (class_ != null) {
		if (Object.keys(class_["info"]).includes(qlesson)) { return; }
		j["lesson"] = qlesson
	}

	$.ajax({
		url: host + "classes/",
		type: "GET",
		data: j,
		success: function (msg) {
			if (class_ == null) {
				class_ = msg
				class_["info"] = {}

				display_lessons()
				// display_lesson()
				display_description()
			}
			else {
				class_["info"][qlesson] = msg
				lesson = qlesson
				display_lesson()
			}
		},
		error: function (error) {
			// window.location.pathname = "/classes"
			console.log(error)
		}
	})
}

function display_description() {
	if (class_["description-video"] == "") {
		return ;
	}

	$("#a")[0].innerHTML = "";
	$("#lesson-dropdown")[0].innerHTML = `課程介紹 <i class="fa fa-sort-asc" aria-hidden="true"></i>`
	$("#buttons")[0].innerHTML = ""
	lesson = -1

	a = format(videoblock, class_["description-video"])
	$("#video")[0].innerHTML = a;
	$("#classname-now")[0].innerHTML = "";
}

function display_lessons() {
	if (class_["description-video"] != "") {
		b = "<li><a onclick=\"display_description()\">課程介紹</a></li>\
	    <li role=\"separator\" class=\"divider\"></li>"
	}
	else {
		b = ""
	}
	for (i=0;i<class_["length"];i++) {
		if (class_.hasOwnProperty("titles")) {
			if (class_["titles"][i] != undefined) {
				b += format(lessonblock, i, class_["titles"][i]);
				continue
			}
		}
		b += format(lessonblock, i, "課程" + (i + 1));
	}
	$("#lessons")[0].innerHTML = b;
}

function display_lesson() {
	l = class_["info"][lesson]
	oneblock = 90 / l.length;

	b = "";
	for (i=0;i<l.length;i++) {
		if (l[i]["answer"] != "") {
			b += format(classblock, oneblock, i + 1, l[i]["class_name"], i, "block");
			continue
		}
		b += format(classblock, oneblock, i + 1, l[i]["class_name"], i, "none");
	}
	$("#a")[0].innerHTML = b;
	if (class_.hasOwnProperty("titles")){
		if (class_["titles"][lesson] != undefined) {
			$("#lesson-dropdown")[0].innerHTML = class_["titles"][lesson] +
				` <i class="fa fa-sort-asc" aria-hidden="true"></i>`
		}
		else {
			$("#lesson-dropdown")[0].innerHTML = "課程" + (lesson + 1) +
				` <i class="fa fa-sort-asc" aria-hidden="true"></i>`
		}
	}
	else {
		$("#lesson-dropdown")[0].innerHTML = "課程" + (lesson + 1) +
			` <i class="fa fa-sort-asc" aria-hidden="true"></i>`
	}

	video = 0
	display_video()
}

function display_video() {
	classvideo = class_["info"][lesson][video]
	if (classvideo["video"].indexOf("youtube") > -1) {
		a = format(videoblock, classvideo["video"])
	}
	else {
		a = format(privatevideoblock, window.location.host, getCookie("key"), classvideo["video"], "")
		if (classvideo["answer"] != "") {
			a = format(privatevideoblock, window.location.host, getCookie("key"), classvideo["video"], classvideo["answer"])
		}
	}

	$("#video")[0].innerHTML = a;
	$("#classname-now")[0].innerHTML = classvideo["class_name"];

	buttons = ""
	button = classvideo["buttons"]
	for (i=0; i<button.length; i++) {
		buttons += format(buttonblock, button[i][0], button[i][1])
	}
	$("#buttons")[0].innerHTML = buttons
}

function video_jump(classnumber) {
	video = classnumber;
	display_video();
}

function prev() {
	if (video > 0) {
		video -= 1;
		display_video();
	} 
}

function next() {
	if (video < class_["info"][lesson].length - 1) {
		video += 1;
		display_video();
	} 
}

function showanswer(classnumber) {
	video = classnumber;

	link = class_["info"][lesson][video]["answer"]
	if (link.indexOf("youtube") > -1) {
		a = format(videoblock, link)
	}
	else {
		a = format(privatevideoblock, window.location.host, getCookie("key"), link)
	}

	a += format(questionblock, video)

	$("#video")[0].innerHTML = a;
	$("#classname-now")[0].innerHTML = class_["info"][lesson][video]["class_name"] + " 解答";
}

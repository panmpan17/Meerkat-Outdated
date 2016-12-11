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

//  onmouseover="\
// document.getElementById('classname').innerHTML\
//  = '{2}';show('classname');" onmouseout="hide('classname');"\
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

var lessonblock = `<li><a onclick="lesson={0};display_lesson()">{1}</a></li>`

var questionblock = `<br /><br />
<div style="text-align: left;">
<a onclick="video_jump({0})"><button class="btn btn-primary">問題</button></a>
</div>
`

function loadclass(classname) {
	j = {"class":classname}
	key = getCookie("key")
	if (key != "") {
		j["key"] = key
	}
	$.ajax({
		url: host + "classes/",
		type: "GET",
		data: j,
		success: function (msg) {
			class_ = msg
			display_lessons()
			display_lesson()
			display_description()
		},
		error: function (msg) {
			window.location.pathname = "/classes"
		}
	})
}

function display_description() {
	if (class_["description-video"] == "") {
		return ;
	}

	document.getElementById("a").innerHTML = "";
	document.getElementById("lesson-dropdown").innerHTML = `課程介紹 <i class="fa fa-sort-asc" aria-hidden="true"></i>`
	document.getElementById("buttons").innerHTML = ""
	lesson = -1

	a = format(videoblock, class_["description-video"])
	document.getElementById("video").innerHTML = a;
	document.getElementById("classname-now").innerHTML = "";
}

function display_lessons() {
	l = class_["info"]
	if (class_["description-video"] != "") {
		b = "<li><a onclick=\"display_description()\">課程介紹</a></li>\
	    <li role=\"separator\" class=\"divider\"></li>"
	}
	else {
		b = ""
	}
	for (i=0;i<l.length;i++) {
		if (class_.hasOwnProperty("titles")) {
			if (class_["titles"][i] != undefined) {
				b += format(lessonblock, i, class_["titles"][i]);
				continue
			}
		}
		b += format(lessonblock, i, "課程" + (i + 1));
	}
	document.getElementById("lessons").innerHTML = b;
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
	document.getElementById("a").innerHTML = b;
	if (class_.hasOwnProperty("titles")){
		if (class_["titles"][lesson] != undefined) {
			document.getElementById("lesson-dropdown").innerHTML = class_["titles"][lesson] +
				` <i class="fa fa-sort-asc" aria-hidden="true"></i>`
		}
		else {
			document.getElementById("lesson-dropdown").innerHTML = "課程" + (lesson + 1) +
				` <i class="fa fa-sort-asc" aria-hidden="true"></i>`
		}
	}
	else {
		document.getElementById("lesson-dropdown").innerHTML = "課程" + (lesson + 1) +
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

	document.getElementById("video").innerHTML = a;
	document.getElementById("classname-now").innerHTML = classvideo["class_name"];

	buttons = ""
	button = classvideo["buttons"]
	for (i=0; i<button.length; i++) {
		buttons += format(buttonblock, button[i][0], button[i][1])
	}
	document.getElementById("buttons").innerHTML = buttons
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

	document.getElementById("video").innerHTML = a;
	document.getElementById("classname-now").innerHTML = class_["info"][lesson][video]["class_name"] + " 解答";

	// buttons = ""
	// button = class_["info"][lesson][video]["buttons"]
	// for (i=0; i<button.length; i++) {
	// 	buttons += format(buttonblock, button[i][0], button[i][1])
	// }
	// document.getElementById("buttons").innerHTML = buttons
}

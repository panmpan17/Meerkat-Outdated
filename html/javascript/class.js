var class_ = null;

var lesson = 0
var video = 0

var classblock = "<div class=\"class_block\" onmouseover=\"\
document.getElementById('classname').innerHTML\
 = '{2}';show('classname');\" onmouseout=\"hide('classname');\"\
  style=\"width:{0}%\" onclick=\"video_jump({3})\">{1}</div>";

var videoblock = "<div class=\"embed-responsive embed-responsive-16by9\">\
 <iframe src=\"{0}&amp;showinfo=0\" frameborder=\"0\" allowfullscreen></iframe></div>"

var privatevideoblock = "<div class=\"embed-responsive embed-responsive-16by9\">\
<iframe src='http://{0}/video/{1}?video={2}'></div>"

var buttonblock = "<a target=\"_blank\" href=\"{1}\">\
 <button class=\"btn btn-primary\">{0}</button></a>"
var lessonblock = "<li><a onclick=\"lesson={0};display_lesson()\">{1}</a></li>"

function loadclass(classname) {
	$.ajax({
			url: host + "classes/",
			type: "GET",
			data: {"class":classname},
			success: function (msg) {
				class_ = msg
				display_lessons()
				display_lesson()
			},
			error: function (msg) {
				console.log(msg);
			}
		}) 
}

function display_description() {

	document.getElementById("a").innerHTML = "";
	document.getElementById("lesson-dropdown").innerHTML = "課程介紹"
	document.getElementById("buttons").innerHTML = ""

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
		b += format(lessonblock, i, "課程" + (i + 1));
	}
	document.getElementById("lessons").innerHTML = b;
}

function display_lesson() {
	l = class_["info"][lesson]
	oneblock = 90 / l.length;

	b = "";
	for (i=0;i<l.length;i++) {
		b += format(classblock, oneblock, i + 1, l[i]["class_name"], i);
	}
	document.getElementById("a").innerHTML = b;
	document.getElementById("lesson-dropdown").innerHTML = "課程 " + (lesson + 1)

	video = 0
	display_video()
}

function display_video() {
	link = class_["info"][lesson][video]["video"]
	if (link.indexOf("youtube") > -1) {
		a = format(videoblock, link)
	}
	else {
		a = format(privatevideoblock, window.location.host, getCookie("key"), link)
	}
	document.getElementById("video").innerHTML = a;
	document.getElementById("classname-now").innerHTML = class_["info"][lesson][video]["class_name"];

	buttons = ""
	button = class_["info"][lesson][video]["buttons"]
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

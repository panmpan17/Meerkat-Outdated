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

class_ = null;

lesson = 0
video = 0
evaluation_try = 0

classblock = `<div class="class_block"\
 style="width:{0}%" onclick="video_jump({3})" id="class_block-{3}">{1}<div id="answer" style="display: {4}"></div></div>`;

videoblock = `<div class=\"embed-responsive embed-responsive-16by9\">
<iframe id="videoframe" src=\"{0}&amp;showinfo=0\" frameborder=\"0\" allowfullscreen></iframe>
</div>`

privatevideoblock = `<div class=\"embed-responsive embed-responsive-16by9\">
<iframe id="videoframe" src='http://{0}/video/{1}?video={2}&nextvid={3}'></iframe>
</div>`

buttonblock = `<a target=\"_blank\" href=\"{1}\">
<button class=\"btn btn-primary\">{0}</button></a>`

lessonblock = `<li><a onclick="loadclass(subject_id, {0})">{1}</a></li>`

questionblock = `<br /><br />
<div style="text-align: left;">
<a onclick="video_jump({0})"><button class="btn btn-primary">問題</button></a>
</div>
`

// load class info
function loadclass(classname, qlesson=-1) {
	j = {"class":classname}
	key = getCookie("key")
	if (key != "") {
		j["key"] = key
	}

	if (class_ != null && qlesson == -1) { return; }
	if (class_ != null) {
		if (class_["info"][qlesson] != undefined) {
			lesson = qlesson
			display_lesson()
			return;
		}
		j["lesson"] = qlesson
	}

	if (getCookie("teacher-key") != "") {
		j["tkey"] = getCookie("teacher-key")
	}

	if (class_ != null) {
		j["cls_per_key"] = class_["key"]
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
				display_description()

				limit = class_["progress"]
				if (limit == undefined) {
					return;
				}
				lesson = 1
				$.each(class_["lesson_length"], function (_, i) {
					if (limit > i) {
						limit -= i
					}
					else {
						return false;
					}
					lesson ++
				})
			}
			else {
				class_["info"][qlesson] = msg
				lesson = qlesson
				display_lesson()
			}
		},
		error: function (error) {
			window.location.pathname = "/classes"
			// console.log(error)
		}
	})
}

// show descripttion video
function display_description() {
	if (class_["description-video"] == "") {
		loadclass(subject_id, 0)
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

//render lessons button dropdown
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

// render lesson bar
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

	$("#class_block-0")[0].classList.add("active")
}

// show single video
function display_video() {
	if ($(".class_block.active").length > 0) {
		$(".class_block.active")[0].classList.remove("active")
	}
	$("#class_block-" + video)[0].classList.add("active")

	classvideo = class_["info"][lesson][video]
	$("#classname-now")[0].innerHTML = classvideo["class_name"];

	if (classvideo["type"] == "video") {
		if (classvideo["video"].indexOf("youtube") > -1) {
			a = format(videoblock, classvideo["video"])
		}
		else {
			if (classvideo["answer"] != "") {
				a = format(privatevideoblock, window.location.host, class_["key"], classvideo["video"], classvideo["answer"])
			}
			else {
				a = format(privatevideoblock, window.location.host, class_["key"], classvideo["video"], "")
			}

		}
		$("#video")[0].innerHTML = a;

		buttons = ""
		button = classvideo["buttons"]
		for (i=0; i<button.length; i++) {
			buttons += format(buttonblock, button[i][0], button[i][1])
		}
		$("#buttons")[0].innerHTML = buttons
	}
	else if (classvideo["type"] == "evaluation") {
		$("#video")[0].innerHTML = evaluation_html(classvideo["questions"]);
		evaluation_try = 0
	}
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

question_format = `<div class="question" id="q-{2}">
	<spawn class="title">{0}</spawn>
	<br><br>
	{1}
</div>`

checkbox_format = `<div>
	<input name="q-{0}" id="q-{0}-{1}" value="{1}" type="checkbox">
	<label for="q-{0}-{1}"><div class="checkbox"></div>{2}</label><br>
</div>`

radio_format = `<div>
	<input name="q-{0}" id="q-{0}-{1}" value="{1}" type="radio">
	<label for="q-{0}-{1}"><div class="radio"></div>{2}</label><br>
</div>`

evaluation_btns = `
<button class="submit" onclick="check_evaluation_answer()">檢查答案</button>
<button id="eval_answer_btn" class="answer" hidden onclick="alert('敬請期待 !!')">看答案</button>
</div>`

function evaluation_html(questions) {
	test_html = `<div id="test">`
	$.each(questions, function (i, question) {
		choices = ""
		$.each(question["choice"], function (e, choice) {
			choice_html = choice.replace(/&/, "&amp;")
			choice_html = choice_html.replace(/</, "&lt;")
			choice_html = choice_html.replace(/>/, "&gt;")
			if (question["answer"].length > 1) {
				choices += format(checkbox_format,
					i + 1,
					e,
					choice_html)
			}
			else {
				choices += format(radio_format, i + 1,
					e,
					choice_html)
			}
		})

		test_html += format(question_format, (i + 1) + ". " + question["question"],
			choices,
			i + 1)
	})
	return test_html + evaluation_btns
}

function check_evaluation_answer() {
	classvideo = class_["info"][lesson][video]
	questions = classvideo["questions"]
	choices = []
	for (i=1;i<=classvideo["questions"].length;i++) {
		values = $(format("[name=q-{0}]:checked", i))

		checked = []
		$.each(values, function (_, e) {
			checked.push(parseInt(e.value))
		})
		if (checked.length == 0) {
			alert("請檢查所有問題都有回答")
			return;
		}
		choices.push(checked.sort())
	}
	evaluation_try += 1

	wrong = []
	right = []
	$.each(choices, function (i, choice) {
		equals = choice.equals(questions[i]["answer"])
		if (equals) {
			right.push(i)
		}
		else {
			wrong.push(i)
		}
	})

	if (wrong.length == 0) {
		// 
		alert("全對")
		$.each($(".question"), function (_, i) {
			i.style.background = "white"
		})
	}
	else {
		alert("有些沒答對, 請仔細檢查錯誤的題目 !")
		if (evaluation_try >= 2) {
			$("#eval_answer_btn").show()
		}

		$.each(right, function (_, i) {
			$(format("#q-{0}", i + 1))[0].style.background = "white"
		})

		$.each(wrong, function (_, i) {
			$(format("#q-{0}", i + 1))[0].style.background = "rgba(255, 117, 91, 0.3)"
		})
	}
}


subject_id = $("#subject_id")[0].textContent
loadclass(subject_id)
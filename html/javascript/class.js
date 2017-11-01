var class_ = null;
var lesson = 0
var video = 0

var videoblock = `<div class="embed-responsive embed-responsive-16by9">
<iframe id="videoframe" src="{0}&amp;showinfo=0" frameborder="0" allowfullscreen></iframe>
</div>`

var privatevideoblock = `<div class="embed-responsive embed-responsive-16by9">
<iframe id="videoframe" src='http://{0}/video/{1}?video={2}'></iframe>
</div>`

var lsn_bar_lsn = `<div id="lesson-{0}" class="lesson shrink">
	<div class="title" onclick="toggle_lsn_btn({0}, this)">{1}</div>
	<div id="lesson-{0}-video" class="video-bar"></div>
</div>`

var lsn_bar_vid = `<div id="vid-{1}-{2}" class="video" onclick="video_jump({1}, {2})">{0}</div>`

// evaluation_try = 0
// questionblock = `<br /><br />
// <div style="text-align: left;">
// <a onclick="video_jump({0})"><button class="btn btn-primary">問題</button></a>
// </div>
// `

buttonblock = `<a target="_blank" href="{1}">
	<button class="btn">{0}</button>
</a>`

function toggle_menu () {
  $(".menu")[0].classList.toggle('shrink')
  $("#view-block")[0].classList.toggle('shrink')
}

function toggle_lsn_btn (seq, i) {
	if (class_ != null) {
		if (class_["lessons"][seq] != undefined) {
			if (i.parentNode.classList.contains("shrink")) {
				$(".menu .lesson").hide()
				$(i.parentNode).show()
				$("#lesson-" + seq + "-video").show(300)
			}
			else {
				$(".menu .lesson").show()
				$(".menu .lesson .video-bar").hide(300)
			}
			i.parentNode.classList.toggle("shrink")
			return;
		}
	}
	loadclass(subject_id, seq)
	return;
}

// load class info
function loadclass (classname, qlesson=-1) {
	j = {"class":classname}
	key = getCookie("key")
	if (key != "") {
		j["key"] = key
	}

	if (class_ != null && qlesson == -1) { return; }
	if (qlesson != -1) {j["lesson"] = qlesson}

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
				class_["lessons"] = {}

				display_lessons_bar()
				if (class_["description-video"] == "") {
					$("#description").hide()
					console.log(1)
					setTimeout(function () {
						$(".video-bar").css("height", "calc(100% - 50px)")
					}, 400)
				}
				else {
					show_description()
				}
			}
			else {
				class_["lessons"][qlesson] = msg
				lesson = qlesson

				$.each(msg["content"], function (_, i) {
					$("#lesson-" + qlesson + "-video")[0].innerHTML += format(lsn_bar_vid,
						i["class_name"],
						qlesson,
						_)
				})

				lesson_html = $("#lesson-" + qlesson)
				$(".menu .lesson").hide()
				$("#lesson-" + qlesson + "-video").show()
				lesson_html.show()
				lesson_html[0].classList.toggle("shrink")
			}
		},
		error: function (error) {
			window.location.pathname = "/classes"
		}
	})
}

//render lessons bar
function display_lessons_bar() {
	$.each(class_["title"], function (lesson_order, title) {
		$("#lessons_bar")[0].innerHTML += format(lsn_bar_lsn,
			lesson_order,
			title)
	})
	$(".menu .lesson .video-bar").hide(300)
}

// show description video
function show_description() {
	lesson = -1

	video_html = format(videoblock, class_["description-video"])
	$("#view-block #title")[0].innerHTML = "介紹";
	$("#view-block #video")[0].innerHTML = video_html;
	$("#btns")[0].innerHTML = ""
}

// show single video
function show_video() {
	// active video button
	try {
		$(".menu .lesson .video-bar .video.active")[0].classList.remove("active")
	} catch (e) {}

	$("#vid-" + lesson + "-" + video)[0].classList.add("active")

	classvideo = class_["lessons"][lesson]["content"][video]
	$("#view-block #title")[0].innerHTML = classvideo["class_name"];

	if (classvideo["type"] == "video") {
		if (classvideo["video"].indexOf("youtube") > -1) {
			video_html = format(videoblock, classvideo["video"])
		}
		else {
			video_html = format(privatevideoblock,
				window.location.host,
				class_["key"],
				classvideo["video"])

		}
		$("#view-block #video")[0].innerHTML = video_html;

		// display buttons
		buttons_html = ""
		$.each(classvideo["buttons"], function (_, i) {
			buttons_html += format(buttonblock, i[0], i[1])
		})
		$("#btns")[0].innerHTML = buttons_html

		$("#prev")[0].innerText = "< Prev"
		$("#prev")[0].onclick = prev
		if (classvideo["answer"] != "") {
			$("#next")[0].innerText = "Answer >"
			$("#next")[0].onclick = show_answer
		}
		else {
			$("#next")[0].innerText = "Next >"
			$("#next")[0].onclick = next
		}
	}
	// else if (classvideo["type"] == "evaluation") {
	// 	$("#video")[0].innerHTML = evaluation_html(classvideo["questions"]);
	// 	evaluation_try = 0
	// }
}

function show_answer () {
	classvideo = class_["lessons"][lesson]["content"][video]

	if (classvideo["answer"] != "") {
		if (classvideo["answer"].indexOf("youtube") > -1) {
			video_html = format(videoblock, classvideo["answer"])
		}
		else {
			video_html = format(privatevideoblock, window.location.host, class_["key"], classvideo["answer"], "")
		}
		$("#view-block #video")[0].innerHTML = video_html;

		// display buttons
		buttons_html = ""
		$.each(classvideo["buttons"], function (_, i) {
			buttons_html += format(buttonblock, i[0], i[1])
		})
		$("#btns")[0].innerHTML = buttons_html

		$("#prev")[0].innerText = "< Question"
		$("#prev")[0].onclick = show_video
		$("#next")[0].innerText = "Next >"
		$("#next")[0].onclick = next
	}
}

function video_jump(lsn_num, vid_num) {
	lesson = lsn_num
	video = vid_num;
	show_video();
}

function prev () {
	if (video > 0) {
		video -= 1;
		show_video();
	} 
}

function next () {
	try {
		if (video < class_["lessons"][lesson]["content"].length - 1) {
			video += 1;
			show_video();
		}
	} catch (e) {}
}

function link (url) {

}

// question_format = `<div class="question" id="q-{2}">
// 	<spawn class="title">{0}</spawn>
// 	<br><br>
// 	{1}
// </div>`

// checkbox_format = `<div>
// 	<input name="q-{0}" id="q-{0}-{1}" value="{1}" type="checkbox">
// 	<label for="q-{0}-{1}"><div class="checkbox"></div>{2}</label><br>
// </div>`

// radio_format = `<div>
// 	<input name="q-{0}" id="q-{0}-{1}" value="{1}" type="radio">
// 	<label for="q-{0}-{1}"><div class="radio"></div>{2}</label><br>
// </div>`

// evaluation_btns = `
// <button class="submit" onclick="check_evaluation_answer()">檢查答案</button>
// <button id="eval_answer_btn" class="answer" hidden onclick="alert('敬請期待 !!')">看答案</button>
// </div>`

// function evaluation_html(questions) {
// 	test_html = `<div id="test">`
// 	$.each(questions, function (i, question) {
// 		choices = ""
// 		$.each(question["choice"], function (e, choice) {
// 			choice_html = choice.replace(/&/, "&amp;")
// 			choice_html = choice_html.replace(/</, "&lt;")
// 			choice_html = choice_html.replace(/>/, "&gt;")
// 			if (question["answer"].length > 1) {
// 				choices += format(checkbox_format,
// 					i + 1,
// 					e,
// 					choice_html)
// 			}
// 			else {
// 				choices += format(radio_format, i + 1,
// 					e,
// 					choice_html)
// 			}
// 		})

// 		test_html += format(question_format, (i + 1) + ". " + question["question"],
// 			choices,
// 			i + 1)
// 	})
// 	return test_html + evaluation_btns
// }

// function check_evaluation_answer() {
// 	classvideo = class_["info"][lesson][video]
// 	questions = classvideo["questions"]
// 	choices = []
// 	for (i=1;i<=classvideo["questions"].length;i++) {
// 		values = $(format("[name=q-{0}]:checked", i))

// 		checked = []
// 		$.each(values, function (_, e) {
// 			checked.push(parseInt(e.value))
// 		})
// 		if (checked.length == 0) {
// 			alert("請檢查所有問題都有回答")
// 			return;
// 		}
// 		choices.push(checked.sort())
// 	}
// 	evaluation_try += 1

// 	wrong = []
// 	right = []
// 	$.each(choices, function (i, choice) {
// 		equals = choice.equals(questions[i]["answer"])
// 		if (equals) {
// 			right.push(i)
// 		}
// 		else {
// 			wrong.push(i)
// 		}
// 	})

// 	if (wrong.length == 0) {
// 		// 
// 		alert("全對")
// 		$.each($(".question"), function (_, i) {
// 			i.style.background = "white"
// 		})
// 	}
// 	else {
// 		alert("有些沒答對, 請仔細檢查錯誤的題目 !")
// 		if (evaluation_try >= 2) {
// 			$("#eval_answer_btn").show()
// 		}

// 		$.each(right, function (_, i) {
// 			$(format("#q-{0}", i + 1))[0].style.background = "white"
// 		})

// 		$.each(wrong, function (_, i) {
// 			$(format("#q-{0}", i + 1))[0].style.background = "rgba(255, 117, 91, 0.3)"
// 		})
// 	}
// }


$(document).ready(function () {
	subject_id = $("#subject_id")[0].textContent
	loadclass(subject_id)

	document.onkeydown = function (e) {
	    e = e || window.event;
	    e = e.keyCode

	    if (e == 37) {
	        prev();
	    }
	    if (e == 39) {
	        next();
	    }
	}
})
var class_ = null;
var lesson = 0
var video = 0
var sections_active = null;

var videoblock = `<iframe id="videoframe" src="{0}&amp;showinfo=0" frameborder="0" allowfullscreen></iframe>`

var privatevideoblock = `<iframe id="videoframe" class="python" src='http://{0}/video/{1}?video={2}' allowfullscreen></iframe>`

var lsn_bar_lsn = `<div id="lesson-{0}" class="lesson shrink{2} {3}">
	<div class="title" onclick="toggle_lsn_btn({0}, this)">{1}</div>
	<div id="lesson-{0}-video" class="video-bar"></div>
</div>`

var lsn_bar_vid = `<div id="vid-{1}-{2}" class="video{3}" onclick="video_jump({1}, {2})">{0}</div>`

var lsn_bar_section_vid = `<div id="vid-{1}-{2}-{3}" class="video" onclick="section_video_jump({1}, {2}, {3})">{0}</div>`

var chose_video_div = `<div class="thumbnail">
	<center>
		<div class="title">
			{1}
		</div>
		<img src="{0}">
	</center>
	<div class="btns">
		<div class="btn bts btn-default" onclick="show_pop_video('{3}')">
			了解功能
		</div>
		<div class="btn bts btn-orange" onclick="redirect_lesson('{2}')" style="right: 0">
			進入挑戰
		</div>
	</div>
</div>`

uniq_images = [
	"/html/images/unic/unic-1.png",
	"/html/images/unic/unic-2.png",
	"/html/images/unic/unic-3.png",
	"/html/images/unic/unic-4.png",
	"/html/images/unic/unic-5.png",
]

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
  $("#toggle_btn")[0].classList.toggle("back")
  resize_video_frame()
}

function toggle_lsn_btn (seq, i) {
	if (class_ != null) {
		if (class_["lessons"][seq] != undefined) {
			if (i.parentNode.classList.contains("shrink")) {
				$(".menu .lesson").hide()
				$(i.parentNode).show()
				$("#lesson-" + seq + "-video").show(300)

				if (sections_active != null) {
					if (seq == sections_active["lesson"]) {
						$(".video-bar > .video:not(.section)").hide();
					}
					else {
						$(".video-bar > .video:not(.section)").show();
					}
				}
			}
			else {
				$(i.parentNode).hide()
				$(".menu .lesson:not(.myhide)").show()
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
	j = {
		"class": classname,
		"clsrid": getCookie("clsrid")
	}
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
			console.log(msg)
			if (msg["success"] != undefined) {
				if (!msg["success"]) {
					if (msg["reason"] == "trial key") {
						alert("這只是體驗課程, 要看更多課程請購買課程")
					}
					return;
				}
			}
			if (class_ == null) {
				class_ = msg
				class_["lessons"] = {}

				display_lessons_bar()
				if (class_["description-video"] == "") {
					$("#description").hide()
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

				html = ""//
				$.each(msg["content"], function (_, i) {
					if (i["type"] != "sections") {
						html += format(lsn_bar_vid,
							i["class_name"],
							qlesson,
							_,
							"")
					}
					else {
						html += format(lsn_bar_vid,
							i["class_name"],
							qlesson,
							_,
							" section")
					}
				})

				html += `<div class="section"></div>`
				$("#lesson-" + qlesson + "-video")[0].innerHTML = html
				lesson_html = $("#lesson-" + qlesson)
				$(".menu .lesson").hide()
				$("#lesson-" + qlesson + "-video").show()
				lesson_html.show()
				lesson_html[0].classList.toggle("shrink")
			}
		},
		error: function (err) {
			storeCookie("teacher-id", "")
			storeCookie("teacher-key", "")
			storeCookie("teacher-userid", "")
			storeCookie("id", "")
			storeCookie("key", "")
			storeCookie("userid", "")
			// console.log(err)
			window.location.pathname = "/classes"
		}
	})
}

//render lessons bar
function display_lessons_bar() {
	$.each(class_["title"], function (lesson_order, title) {
		if (class_["key_type"] != "trial") {
			$("#lessons_bar")[0].innerHTML += format(lsn_bar_lsn,
				lesson_order,
				title["title"],
				"",
				"")
		}
		else {
			// console.log(clas_["trial"], title["title"])
			if (class_["trial"].includes(title["title"])){
				$("#lessons_bar")[0].innerHTML += format(lsn_bar_lsn,
					lesson_order,
					title["title"],
					"",
					"")
			}
			else {
				$("#lessons_bar")[0].innerHTML += format(lsn_bar_lsn,
					lesson_order,
					title["title"],
					"",
					"disabled")
			}
		}
	})
	$(".menu .lesson .video-bar").hide(300)
}

// show description video
function show_description() {
	lesson = -1

	if (class_["description-video"].indexOf("youtube") != -1) {
		video_html = format(videoblock, class_["description-video"])
	}
	else {
		video_html = format(privatevideoblock,
			window.location.host,
			class_["key"],
			class_["description-video"])
	}
	
	$("#view-block #title")[0].innerHTML = "介紹";
	$("#view-block #video")[0].innerHTML = video_html;
	$("#btns")[0].innerHTML = ""
	resize_video_frame();
}

// show single video
function show_video() {
	classvideo = class_["lessons"][lesson]["content"][video]
	video_id = format("#vid-{0}-{1}", lesson, video)

	if ((classvideo["type"] != "redirect") && (classvideo["type"] != "sections")) {
		// active video button
		try {$(".menu .lesson .video-bar .video.active")[0].classList.remove("active")
		} catch (e) {}

		$(video_id)[0].classList.add("active")
		$("#view-block #title")[0].innerHTML = classvideo["class_name"];
	}

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
	else if (classvideo["type"] == "evaluation") {
		$("#view-block #video")[0].innerHTML = evaluation_html(classvideo["questions"]);
		evaluation_try = 0
	}
	else if (classvideo["type"] == "chosevideo") {
		html = `<center>`;
		num = 0
		$.each(classvideo["choice"], function (_, choice) {
			html += format(
				chose_video_div,
				uniq_images[num],
				choice["intro"],
				choice["redirect"],
				choice["video"],
				)
			num += 1
			if (num == uniq_images.length) {
				num = 0
			}
		})
		html += "</center>";
		$("#view-block #video")[0].innerHTML = html
	}
	else if (classvideo["type"] == "redirect") {
		$(".lesson:not(.shrink)")[0].classList.add("shrink")
		$.each(class_["title"], function (order, title) {
			if (classvideo["redirect"] == title["title"]) {
				toggle_lsn_btn(order, $(".title")[order])
			}
		})
	}
	else if (classvideo["type"] == "sections") {
		try {$(".menu .lesson .video-bar .video.active")[0].classList.remove("active")
		} catch (e) {}

		$(video_id)[0].classList.add("active")

		section_html = $("#lesson-" + lesson +"-video .section:not(.video)")

		shrink_section = false
		if (sections_active != null) {
			if ((sections_active["lesson"] == lesson) && (sections_active["video"] == video)) {
				shrink_section = true
			}
		}

		if (!shrink_section) {
			$(".video").hide(300);
			$(video_id).show(300);

			html = ""
			$.each(classvideo["content"], function (_, i) {
				html += format(lsn_bar_section_vid,
					i["class_name"],
					lesson,
					video,
					_)
			})
			section_html[0].innerHTML = html
			sections_active = {
				"lesson": lesson,
				"video": video,
				"index": 0,
			}
		}
		else {
			$(".video.section").hide(300)
			$(".video:not(.section)").show(300);

			section_html[0].innerHTML = ""
			$(video_id)[0].classList.remove("active");
			sections_active = null;
		}
	}
	resize_video_frame();
}

function section_video_jump (lesson, video, section_index) {
	sections_active["index"] = section_index
	classvideo = class_["lessons"][lesson]["content"][video]["content"][section_index]
	video_id = format("#vid-{0}-{1}-{2}", lesson, video, section_index)
	$("#view-block #title")[0].innerHTML = classvideo["class_name"];

	try {$(".menu .lesson .video-bar .video.active:not(.section)")[0].classList.remove("active")
	} catch (e) {}

	$(video_id)[0].classList.add("active")

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
	resize_video_frame();
}

function redirect_lesson (lesson_name) {
	$.each(class_["lessons"][lesson]["content"], function (order, title) {
		if (lesson_name == title["class_name"]) {
			video_jump(lesson, order)
			section_video_jump(lesson, order, 0)
		}
	})
}

function show_pop_video (video_url) {
	$("#intro-video-frame").modal("show");
	$("#intro-video")[0].src = format(
		"http://{0}/video/{1}?video={2}",
		window.location.host,
		class_["key"],
		video_url,
		);
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
	classvideo = class_["lessons"][lesson]["content"][video]
	if (video > 0) {
		if (classvideo["type"] != "sections") {
			video -= 1;
			show_video();
		}
	}

	if (classvideo["type"] == "sections") {
		if (sections_active["index"] > 0) {
			section_video_jump(sections_active["lesson"],
				sections_active["video"],
				sections_active["index"] - 1)
		}
	}
}

function next () {
	try {
		classvideo = class_["lessons"][lesson]["content"][video]
		if (video < class_["lessons"][lesson]["content"].length - 1) {
			if (classvideo["type"] != "sections") {
				video += 1;
				show_video();
				return;
			}
		}

		if (classvideo["type"] == "sections") {
			if (sections_active["index"] < classvideo["content"].length - 1) {
				section_video_jump(sections_active["lesson"],
					sections_active["video"],
					sections_active["index"] + 1)
			}
		}
	} catch (e) {}
}

function link (url) {

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
	classvideo = class_["lessons"][lesson]["content"][video]
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

	if (class_["key_type"] == "user") {
		answers = []
		$.each(choices, function (_, i) {
			answers.push(i.join(""))
		})
		answers = answers.join("a")
		$.ajax({
			url: host + "classroom/form",
			type: "POST",
			dataType: "json",
			data: JSON.stringify({
				"key": getCookie("key"),
				"form": classvideo["class_name"],
				"folder": class_["folder"],
				"answer": answers,
			}),
			contentType: "application/json; charset=utf-8",
			success: function (msg) {
				console.log(msg)
			},
			error: function (error) {
				console.log(error)
			}
		})
	}

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

function resize_video_frame () {
	width = $(document).width()
	height = $(document).height()

	try {
		if ($(".menu")[0].classList.contains("shrink")) {
			$("#videoframe")[0].style.width = (width - 20) + "px"
		}
		else {
			$("#videoframe")[0].style.width = (width - 320) + "px"
		}
		$("#videoframe")[0].style.height = (height - 170) + "px"
	} catch (e) {}
}

$(document).ready(function () {
	subject_id = $("#subject_id")[0].textContent

	// if (getCookie("clsrid") == "" && getCookie("teacher-key") != "") {
	// 	window.location.pathname = "/classes"
	// }
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

	$(window).resize(resize_video_frame)
})
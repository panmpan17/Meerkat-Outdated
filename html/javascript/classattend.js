comments = {}
classrooms = {}
homeworks = {}
file_record = {}
classroomnames = $("#classroomnames")[0]

a2z = "abcdefghijklmnopqrstuvwxyz"
classroom_homwork_format = `
<div class="classroom-card">
<b>{0}</b>
{3}
<br />
<img class="card-img" src="/html/images/class/{1}.png" alt="" />
<table class="table homework">
<thead>
<tr id="thead-{2}"></tr>
</thead>
<tbody>
<tr id="tbody-{2}"></tr>
</tbody>
</table>
<div id="homeworkshelf-{2}"></div>
</div>
<br /><br />
`

picture_fromat = `\
<div>
<a style="cursor: pointer" onclick="play_scratch_project('{0}', '{1}', '{2}')">
	<img src="//cdn2.scratch.mit.edu/get_image/project/{0}_144x108.png" style="border: 1px rgba(50, 50, 50, 0.5) solid;"/>
</a>
</div>`

PY_FILE_HW = `<div class="py_file_hw" onclick="show_file('{0}')">
	{0}
</div>`

PY_UNIT_BTN = `<br><div class="dropdown">
	<button type="button" class="btn btn-default btn-lg dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
	課程 <span id="lessonbtn"></span> <i class="fa fa-sort" aria-hidden="true"></i>
</button>
<ul class="dropdown-menu">`

project_embed_fromat = "//scratch.mit.edu/projects/embed/{0}/?autostart=false"
python_homework_re = new RegExp("(test|hw)1?[0-9]-[0-9]{1,2}\.py")
project_page_format = "https://scratch.mit.edu/projects/{0}/"
nav_format = `<li role="presentation" onclick="showclassroom('{1}')"><a>{0}</a></li>`

function loadclassroom() {
	files = {}
	$.ajax({
		url: host + "classroom/",
		cache: false,
		type: "GET",
		data: {"key": getCookie("key")},
		success: function (msg) {
			$.each(msg, function (i) {
				classroomnames.innerHTML += format(nav_format,
					msg[i]["name"],
					msg[i]["id"])
				classrooms[msg[i]["id"]] = msg[i]
			})

			if (msg.length > 0) {
				showclassroom(msg[0]["id"]);
			}
			else {
				showactivity();
			}
		},
		error: function (msg) {
			reload = confirm("請重新登錄");
			if (reload) {
				show("login-frame");
			}
		}
	})
}

function showclassroom(cls_id) {
	classroom = classrooms[cls_id];
	$("#hw-view").show();
	$("#activities-type").hide();
	$("#activity-view").hide();
	$("#activity-list").hide();
	$("#classroom-name").html(classroom["name"]);
	$("#classroom-type").html(classroom["type"]);

	if (classroom["type"].indexOf("scratch") != -1) {
		$("#fileupload").hide();

		t_l = classroom["type"].split("_");
		s_level = a2z[t_l[1] - 1];

		$("#classroom-name").html(classroom["name"] + " (" + s_level.toUpperCase() + ")");

		s_projct_match = RegExp("[" + s_level + s_level.toUpperCase() + "][0-9]{1,3}\-");
		loadscratchhomwork(classroom["student_cid"], cls_id);
	}
	else if (classroom["type"].indexOf("python") != -1) {
		$("#fileupload").show();
		$("[name=clsroomid]")[0].value = cls_id;

		loadfilehomework(classroom["folder"], cls_id);
	}

	$.ajax({
		url: host + "classroom/check_folder",
		cache: false,
		data: {
			"folder": classroom["folder"],
			"key": getCookie("key")},
		success: function (msg) {
			$("#filelist")[0].innerHTML = ""
			$.each(msg, function (_, i) {
				$("#filelist")[0].innerHTML += format(
					`<li class='filelist'><a href="/downloadfile/{0}/teacher/{1}" style="color:black" target="_blank">{1}</a></li>`,
					classroom["folder"],
					i)
			})
		}})
}

function loadscratchhomwork(student_id, cls_id) {
	loadcomment(cls_id)
	$.ajax({
		url: "https://scratch.mit.edu/users/" + student_id + "/projects/",
		cache: false,
		success: function (msg) {
			homework = new Set();
			text = msg;
			find = text.indexOf(`<span class="title">`);

			projects = {}
			if (find != -1) {
				while (find >= 0) {
					find = text.indexOf(`<span class="title">`)
					text = text.substring(find + 1)
					if (find >= 0){
						project = text.substring(text.indexOf("/projects/") + 10, text.indexOf("</a>"))
						project = project.split('"')
						
						project_id = project[0].substring(0, project[0].length - 1)
						project_title = project[1].substring(1)

						if (s_projct_match.test(project_title)) {
							project_title = s_projct_match.exec(project_title)[0]
							project_title = project_title.substring(1, project_title.length - 1)

							projects[project_title] = project_id
							homework.add(project_title)
						}
					}
				}
			}

			homework = Array.from(homework).sort()

			thead = ""
			tbody = ""
			slide = ""
			$.each(homework, function (i) {
				if (slide == "") {
					slide = `<section class="regular slider" id="s{0}">`
				}
				slide += format(picture_fromat,
					projects[homework[i]],
					cls_id,
					homework[i])
				thead += `<th style="text-align:center">` + homework[i] + "</th>";
				tbody += `<td style="font-size: 15px;">&#10004;</td>`
			})
			if (slide != "") {
				slide += "</section><br>"
			}

			$("#hw-thead")[0].innerHTML = thead
			$("#hw-tbody").html(tbody)
			$("#hw-shelf").html(format(slide, cls_id))
			homeworks[cls_id] = homework

			setTimeout(function () {
				$("#s" + cls_id).slick({
					dots: true,
					infinite: true,
					slidesToShow: 3,
					slidesToScroll: 3
				});
			}, 100);
		}
	})
}

function play_scratch_project(project_id, cls_id, hw_s) {
	show("project")
	show("scratch_iframe")
	hide("file")

	$("#scratch_iframe")[0].src = format(project_embed_fromat, project_id)
	$("#s_project_page")[0].href = format(project_page_format, project_id)
	$("#hwcomment")[0].innerHTML = ""

	if (comments[cls_id] != undefined) {
		if (comments[cls_id][getCookie("id")]) {
			if (comments[cls_id][getCookie("id")][hw_s] != undefined) {
				comment = comments[cls_id][getCookie("id")][hw_s]
				$("#hwcomment")[0].innerHTML = comment.replace(/\n/g, "<br>")
			}
		}
	}
}

function loadfilehomework(folder, cls_id) {
	loadcomment(cls_id)
	$("#hw-tbody").html("")
	$.ajax({
		url: host + "classroom/check_folder",
		cache: false,
		data: {
			"folder": folder,
			"student": true,
			"cid": getCookie("id"),
			"key": getCookie("key")},
		success: function (msg) {
			file_record = msg
			homework = new Set()
			projects = []
			units = new Set()
			files[cls_id] = {}
			$.each(msg, function (k, v) {
				if (python_homework_re.test(k)) {
					cid_hwn = k.split("_")
					cid = cid_hwn[0]
					hwn = cid_hwn[1]
					if (hwn.indexOf(".") != -1) {
						hwn = hwn.substring(0, hwn.indexOf("."))
					}

					homework.add(hwn)
					units.add(hwn.substring(0, hwn.indexOf("-")))

					files[cls_id][hwn] = k
					projects.push(hwn)
				}
			})

			units = Array.from(units).sort()
			homeworks[cls_id] = homework
			if (units.length > 0) {
				buttonsgroup = PY_UNIT_BTN
				$.each(units, function (_, i) {
					unit = i.replace("test", "課程 ")
					unit = unit.replace("hw", "功課 ")
					f = `<li style="cursor:pointer">\
						<a onclick="changefileunit('{0}','{1}','{2}')">{3}</a></li>`
					buttonsgroup += format(f,
						folder,
						i,
						cls_id,
						unit)
				})
				buttonsgroup += `</ul></div><br>`

				$("#hw-thead")[0].innerHTML = buttonsgroup
				changefileunit(folder, units[0], cls_id)
			}
			else {
				$("#hw-thead")[0].innerHTML = ""
				$("#hw-tbody")[0].innerHTML = "<h5>還沒有上傳任何功課</h5>"
				$("#hw-shelf")[0].innerHTML = ""
			}
		}
	})
}

function changefileunit(folder, unit, cls_id) {
	homework = Array.from(homeworks[cls_id]).sort();
	reg = new RegExp(unit + "-")
	slide = ""
	$.each(homework, function (_, i) {
		if (reg.test(i)) {
			if (slide == "") {
				slide = `<section style="clear: both; padding:10px;">`
			}
			slide += format(PY_FILE_HW,
				i)
		}
	})
	if (slide != "") {
		slide += "</section><br>"
	}
	$("#hw-shelf")[0].innerHTML = slide
}

function howtoupload(type) {
	hide('classroom-frame');
	show('howuploadhomework-frame');

	$(".howtoupload").hide()
	$("#howtoupload-" + type).show()
}

function upload() {
	$("[name=key]")[0].value = getCookie("key")
	$("#homeworkupload")[0].submit()
}

function parse_file(Text) {
	Text = Text.replace(/\</g, "&lt;").replace(/\>/g, "&gt;")
	l = Text.split("\n")

	maxident = l.length.toString().length
	Text = ""
	for (i=0;i<l.length;i++) {
		Text += `<span class="numline">`
		Text += (i + 1) + "&nbsp;&nbsp;"
		Text += "&nbsp;&nbsp;".repeat(maxident - (i + 1).toString().length)
		Text += "|" + "</span>&nbsp;"
		Text += l[i].replace(/ /g, "&nbsp;&nbsp;") + "<br>"
	}
	return Text
}

record_format = "上傳次數: {0}<br>更新上傳時間: {1}"
function show_file(file) {
	show("project")
	$("#file").show();
	$("#scratch_iframe").hide();

	$("#scratch_iframe")[0].src = ""

	filepath = files[classroom["id"]][file]
	updated_time = file_record[filepath]["updated_time"]
	if (updated_time == null) { updated_time = "無紀錄" }

	lastupdate = file_record[filepath]["lastupdate"]
	if (lastupdate == null) { lastupdate = "無紀錄" }

	record = format(record_format,
		updated_time,
		lastupdate,
		)
	$("#hwinfo")[0].innerHTML = record

	
	filname = format("{0}/{1}_{2}.py",
		classroom["folder"],
		getCookie("id"),
		file)
	$("#s_project_page")[0].href = "/downloadfile/" + filname
	$("#hwcomment")[0].innerHTML = ""

	$.ajax({
		url: "downloads/" + filname,
		cache: false,
		success: function (msg) {
			$("#file")[0].innerHTML = parse_file(msg)
		}
	})

	if (comments[cls_id] != undefined) {
		if (comments[cls_id][getCookie("id")]) {
			if (comments[cls_id][getCookie("id")][file] != undefined) {
				comment = comments[cls_id][getCookie("id")][file]
				$("#hwcomment")[0].innerHTML = comment.replace(/\n/g, "<br>")
			}
		}
	}
}

function loadcomment(cls_id) {
	$.ajax({
		url: host + "classroom/comment?cls_id=" + cls_id,
		cache: false,
		success: function (msg) {
			comments[cls_id] = msg
		}
	})
}

function showactivity() {
	year = new Date().getFullYear();
	$("#hw-view").hide()
	$("#activity-view").show()
	$("#activities-type").show()
	$("#activity-list").hide()
	$.ajax({
		url: host + "activity/",
		cache: false,
		data: {"key": getCookie("key"), "year": year},
		success: function (msg) {
			activities["repeat"] = {}
			activities["date"] = {}

			$.each(msg["repeat"], function (i) {
				day = parseInt(msg["repeat"][i]["repeat"])
				if (activities["repeat"][day] == undefined) {
					activities["repeat"][day] = []
				}
				activities["repeat"][day].push(msg["repeat"][i])
			})

			$.each(msg["date"], function (i) {
				month = parseInt(msg["date"][i]["date"].match(/[0-9]+/g)[1])
				if (activities["date"][month] == undefined) {
					activities["date"][month] = []
				}
				activities["date"][month].push(msg["date"][i])
			})
			loadMonth(currentYear, currentMonth);
		}
	})
}

NUM_2_DAY = [
	"一",
	"二",
	"三",
	"四",
	"五",
	"六",
	"日",
]
BLANKDAY = `<div class="blankday"><br></div>\n`
DAY = `<div class="day" id="{0}-{1}-{2}" onclick="showday(this)">{2}{3}</div>\n`
RED_DOT = `<span style="color:yellow">&#9679;</span>`
GREEN_DOT = `<span style="color:orange">&#9679;</span>`
DATE_ACTIVITY = `<div class="date-act">
    <span class="title">{0}</span><br />
    <span class="time">{1} {2}</span><br />
    <span class="addr">{3}</span>
    <div class="summary" onclick="attendquit(this, {6})">{4}</div>
    {5}
</div>`
REPEAT_ACTIVITY = `<div class="repeat-act">
    <span class="title">{0}</span><br />
    <span class="time">每週{1} {2}</span><br />
    <span class="addr">{3}</span>
    <div class="summary">{4}</div>
    {5}
</div>`
ATTEND_BUTTON = `<button class="attend" onclick="attendquit(this, {0})"> 參加 </button>`
QUIT_BUTTON = `<button class="quit" onclick="attendquit(this, {0})"> 退出 </button>`
activities = {}

var currentMonth = new Date().getMonth();
var currentYear = new Date().getFullYear();

function loadMonth(year, month) {
	$("#date")[0].innerHTML = ""
	$("#yearmonth").html(year + " / " + (month + 1))

	maxdays = new Date(year, month + 1, 0).getDate();
	first_day = new Date(year, month, 1).getDay();
	
	if (first_day > 0) {
		day = first_day
		for (i=1;i<first_day;i++) {
			$("#date")[0].innerHTML += BLANKDAY;
		}
	}
	else {
		day = 7
		for (i=1;i<7;i++) {
			$("#date")[0].innerHTML += BLANKDAY;
		}
	}
	

	for (i=1;i<=maxdays;i++) {
		if (activities["repeat"][day] != undefined) {
			$("#date")[0].innerHTML += format(DAY,
				year,
				month + 1,
				i,
				GREEN_DOT.repeat(activities["repeat"][day].length));
		}
		else {
			$("#date")[0].innerHTML += format(DAY,
				year,
				month + 1,
				i,
				"");
		}
		if (day != 7) {
			day ++
		}
		else {
			day = 1
		}
	}
	$("#date")[0].innerHTML += "<br><br>"

	setTimeout(function () {
		acts = activities["date"][month + 1]
		if (acts != undefined) {
			$.each(acts, function (i) {
				date = acts[i]["date"].match(/[0-9]+/g)
				date[1] = parseInt(date[1])
				date[2] = parseInt(date[2])
				eid = date.join("-")
				$("#" + eid)[0].innerHTML += RED_DOT
			})
		}
	}, 500)
}

function addOneMonth() {
	if (currentMonth + 1 < 11) {
		currentMonth ++
	}
	else {
		currentMonth = 0
		currentYear ++
	}
	loadMonth(currentYear, currentMonth)
}

function minusOneMonth() {
	if (currentMonth - 1 >= 0) {
		currentMonth --
	}
	else {
		currentMonth = 11
		currentYear --
	}
	loadMonth(currentYear, currentMonth)
}

function today() {
	var currentMonth = new Date().getMonth();
	var currentYear = new Date().getFullYear();
	loadMonth(currentYear, currentMonth);
}

function showday(e) {
	day = $(e)[0].id.split("-")
	day[0] = parseInt(day[0])
	day[1] = parseInt(day[1])
	day[2] = parseInt(day[2])
	activities_html = $("#activities")[0]
	activities_html.innerHTML = "<h3>" + day.join(" / ") + "</h3>";

	d = new Date(day[0], day[1] - 1, day[2]).getDay()

	if (d != 7) {
		acts = activities["repeat"][d]
	}
	else {
		acts = activities["repeat"][7]
	}
	if (acts != undefined) {
		$.each(acts, function (i) {
			button = ATTEND_BUTTON
			if (acts[i]["participant"].indexOf(parseInt(getCookie("id"))) != -1) {
				button = QUIT_BUTTON
			}
			activities_html.innerHTML += format(REPEAT_ACTIVITY,
				acts[i]["name"],
				NUM_2_DAY[acts[i]["repeat"] - 1],
				acts[i]["time"],
				acts[i]["addr"],
				acts[i]["summary"].replace(/\n/g, "<br>"),
				format(button, acts[i]["id"]))
		})
	}

	acts = activities["date"][day[1]]
	if (acts != undefined) {
		$.each(acts, function (i) {
			date = acts[i]["date"].match(/[0-9]+/g)
			if (day[2] == parseInt(date[2])) {
				button = ATTEND_BUTTON
				if (acts[i]["participant"].indexOf(parseInt(getCookie("id"))) != -1) {
					button = QUIT_BUTTON
				}
				activities_html.innerHTML += format(DATE_ACTIVITY,
					acts[i]["name"],
					acts[i]["date"],
					acts[i]["time"],
					acts[i]["addr"],
					acts[i]["summary"].replace(/\n/g, "<br>"),
					format(button, acts[i]["id"]))
			}
		})
	}
	activities_html.scrollIntoView(true)
}

function attendquit(e, id) {
	json = {
		"key": getCookie("key"),
		"id": id,
		"participant": "",
	}
	$.ajax({
		url: host + "activity/",
		cache: false,
		type: "PUT",
		dataType: "json",
		data: JSON.stringify(json),
		contentType: "application/json; charset=utf-8",
		success: function (msg) {
			type = $(e)[0].classList[0]
			if (type == "attend") {
				$(e)[0].classList = ["quit"]
				$(e)[0].innerHTML = "退出"
			}
			else {
				$(e)[0].classList = ["attend"]
				$(e)[0].innerHTML = "參加"
			}
		},
		error: function (error) {
			reload = confirm("請重新登錄");
			if (reload) {
				show("login-frame");
			}
		}
	})
}

function showparticipant(t) {
	json = {
		"participant": t,
		"key": getCookie("key"),
	}
	$.ajax({
		url: host + "activity/",
		cache: false,
		data: json,
		success: function (msg) {
			$("#activity-list").show()
			$("#activity-view").hide()
			activities_html = $("#activity-list")[0]
			acts = msg

			if (t == "True") {
				activities_html.innerHTML = "<h3>參加的課程</h3>";
			}
			else {
				activities_html.innerHTML = "<h3>未參加的課程</h3>";
			}

			$.each(acts, function (i) {
				if (acts[i]["repeat"] != 0) {
					button = ATTEND_BUTTON
					if (acts[i]["participant"].indexOf(parseInt(getCookie("id"))) != -1) {
						button = QUIT_BUTTON
					}
					activities_html.innerHTML += format(REPEAT_ACTIVITY,
						acts[i]["name"],
						NUM_2_DAY[acts[i]["repeat"] - 1],
						acts[i]["time"],
						acts[i]["addr"],
						acts[i]["summary"].replace(/\n/g, "<br>"),
						format(button, acts[i]["id"]))
				}
				else {
					button = ATTEND_BUTTON
					if (acts[i]["participant"].indexOf(parseInt(getCookie("id"))) != -1) {
						button = QUIT_BUTTON
					}
					activities_html.innerHTML += format(DATE_ACTIVITY,
						acts[i]["name"],
						acts[i]["date"],
						acts[i]["time"],
						acts[i]["addr"],
						acts[i]["summary"].replace(/\n/g, "<br>"),
						format(button, acts[i]["id"]))
				}
			})
			activities_html.innerHTML += `<div style="clear: left"><br></div>`
		},
		error: function (error) {
			reload = confirm("請重新登錄");
			if (reload) {
				show("login-frame");
			}
		}
	})
}

function showpresent(t) {
	json = {
		"present": t,
		"key": getCookie("key"),
	}
	$.ajax({
		url: host + "activity/",
		cache: false,
		data: json,
		success: function (msg) {
			$("#activity-list").show()
			$("#activity-view").hide()
			activities_html = $("#activity-list")[0]
			acts = msg

			if (t == "True") {
				activities_html.innerHTML = "<h3>到場的課程</h3>";
			}
			else {
				activities_html.innerHTML = "<h3>未到場的課程</h3>";
			}

			$.each(acts, function (i) {
				if (acts[i]["repeat"] != 0) {
					activities_html.innerHTML += format(REPEAT_ACTIVITY,
						acts[i]["name"],
						NUM_2_DAY[acts[i]["repeat"] - 1],
						acts[i]["time"],
						acts[i]["addr"],
						acts[i]["summary"].replace(/\n/g, "<br>"),
						"")
				}
				else {
					activities_html.innerHTML += format(DATE_ACTIVITY,
						acts[i]["name"],
						acts[i]["date"],
						acts[i]["time"],
						acts[i]["addr"],
						acts[i]["summary"].replace(/\n/g, "<br>"),
						"")
				}
			})
			activities_html.innerHTML += `<div style="clear: left"><br></div>`
		},
		error: function (error) {
			reload = confirm("請重新登錄");
			if (reload) {
				show("login-frame");
			}
		}
	})
}

$(document).ready(function () {
	loadclassroom();
})
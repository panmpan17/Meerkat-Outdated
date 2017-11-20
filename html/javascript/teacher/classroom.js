chart_ctx = document.getElementById("chart").getContext('2d');
chart = new Chart(chart_ctx, {
	type: 'pie',
	data: {
		datasets: [{
			label: '# of Votes',
			borderWidth: 0
		}]
	},
	options: {}
});;
chart_form = null

classrooms = null;
s_projct_match = null
file_text = "";
files = {};
files_records = {};
file_re = RegExp("[0-9]+_.*");

a2z = "abcdefghijklmnopqrstuvwxyz"
CLASSROOM_F = `<li id="button-classroom-{1}">
	<a onclick="changeclassroom('{1}')">{0}</a>
</li>`
CLASSROOM_MAIN_F = `<hr />
<div class="hover" onclick="changeclassroom('{3}')">
<h4 style="color:royalblue">{0}</h4>
人數: {1}<br>
<span style="color:darkgray">開始時間:</spawn> {2}
</div>`
PROJECT_F = "https://scratch.mit.edu/users/{0}/projects/"

PICTURE_F = `\
<div>
	<a style="cursor: pointer" onclick="playScratchProject('{0}', '{1}', '{2}')">
		<img src="//cdn2.scratch.mit.edu/get_image/project/{0}_144x108.png" style="border: 1px rgba(50, 50, 50, 0.5) solid;"/>
		{3}
	</a>
</div>`
PROJECT_EMBED_F = "//scratch.mit.edu/projects/embed/{0}/?autostart=false"
PROJECT_PAGE_F = "https://scratch.mit.edu/projects/{0}/"

SCRATCH_HW_TB_F = `<td class="hover" onclick="playScratchProject({1}, {2}, {3})">
	<i class="fa fa-check" style="{0}" aria-hidden="true"></i>
</td>`
SC_HW_UNIT_TB_TITLE_F = `<th class="hover" onclick="displayScUnit('{0}')">
	{0}
</th>`
SC_HW_S_TB_SIDE_F = `<tr><td class="hover" onclick="displayScId('{0}')">{1}</td>`


PY_HW_TB_F = `<td class="hover" onclick="showFile('{1}', {2})">
	<i class="fa fa-check" style="{0}" aria-hidden="true"></i>
</td>`
PY_HW_UNIT_TB_TITLE_F = `<th class="hover" onclick="displayPyUnit('{0}')">
	{1}
</th>`
PY_HW_S_TB_SIDE_F = `<tr><td class="hover" onclick="displayPyId('{0}','{1}')">{2}</td>`

RECORD_F = "上傳次數: {0}<br>更新上傳時間: {1}"

function loadallclassroom () {
	$.ajax({
		url: host + "classroom/",
		type: "GET",
		data: {"tkey": getCookie("teacher-key")},
		success: function (msg) {
			if (msg.length == 0) {
				return;
			}
			$("#classrooms")[0].innerHTML = "";

			classrooms = {};
			for (i=0;i<msg.length;i++) {
				$("#classrooms")[0].innerHTML += format(CLASSROOM_F,
					msg[i]["name"],
					msg[i]["id"]);
				$("#classroom-main")[0].innerHTML += format(CLASSROOM_MAIN_F,
					msg[i]["name"],
					Object.keys(msg[i]["students"]).length,
					msg[i]["create_at"],
					msg[i]["id"])
				classrooms[msg[i]["id"]] = msg[i]
			}
		}
	})
}

function changeclassroom (cls_id) {
	$("[class=active]")[0].classList.remove("active");
	$("[class=page-wrapper]").hide();

	$("#button-classroom-" + cls_id)[0].classList.add("active");
	$("#p-classroomview").show();

	classroom = classrooms[cls_id];
	$("#class-name")[0].innerHTML = classroom["name"];
	$("#student-num")[0].innerHTML = classroom["students"].length;
	$("#classroom-type")[0].innerHTML = CLASS_TO[classroom["type"]];

	$("#porjects")[0].innerHTML = "";
	$("#homewrok")[0].innerHTML = "";
	$("#links")[0].innerHTML = "";
	$("#buttonsgroup").html("")
	$("#refreshclassroom")[0].onclick = function () {
		changeclassroom(cls_id);
	}

	homework = new Set();
	students_project = {};
	if (classroom["type"].indexOf("scratch") != -1) {
		loadAllScratchHomework();
	}
	else if (classroom["type"].indexOf("python") != -1) {
		$("#student-num")[0].innerHTML = Object.keys(classroom["students"]).length;
		loadPythonHomework();
	}

	// display links
	$.each(classroom["links"], function (_, i) {
		$('#links').append($(format(`<input name="links" value="{0}" class="form-control" style="width: 80%"><br>`,
			i)))
	})

	loadTeacherFiles()
	loadStudentsGrade()
}

function loadAllScratchHomework () {
	t_l = classroom["type"].split("_")
	s_level = a2z[t_l[1] - 1]

	timesout = 5000
	s_projct_match = RegExp("[" + s_level + s_level.toUpperCase() + "][0-9]{1,3}\-")
	$.each(classroom["students"], function (i, s) {
		loadScratchHomework(
			s[0],
			s[1],
			s[2],
			i)
	})

	countdown = setInterval(function () {
		timesout -= 100
		if (timesout <= 0) {
			clearInterval(countdown);
			homeworks = Array.from(homework).sort();

			thead = "<thead><tr><th>學生 \\ 功課</th>";
			$.each(homeworks, function (_, i) {
				thead += format(SC_HW_UNIT_TB_TITLE_F,
					i)
			})
			thead += "</tr></thead>";

			tbody = "<tbody>"
			comments = classroom["comment"]
			$.each(students_project, function (k,v) {
				s = classroom["students"][k]
				tbody += format(SC_HW_S_TB_SIDE_F,
					k,
					s[0])

				comments_keys = []
				if (classroom["comment"][s[1]] != undefined) {
					comments_keys = Object.keys(classroom["comment"][s[1]])
				}
				$.each(homeworks, function (_, i) {
					h = v[i];
					if (h != undefined) {
						if (comments_keys.includes(i)) {
							tbody += format(SCRATCH_HW_TB_F,
								"color: cornflowerblue",
								h,
								i,
								s[1])
						}
						else {
							tbody += format(SCRATCH_HW_TB_F,
								"",
								h,
								i,
								s[1])
						}
					}
					else {
						tbody += `<td></td>`
					}
				})

				tbody += "</tr>"
			})
			tbody += "</tbody>"

			t = format(`<table class="table homework">{0}{1}</table>`, thead, tbody)
			$("#homewrok")[0].innerHTML = t
			}
			showClassroomJob('homework')
	}, 100)
}

function loadScratchHomework (student_name, cid, student_id, seq) {
	var ajaxTime = new Date().getTime();
	$.ajax({
		url: format(PROJECT_F, student_id),
		success: function (msg) {
			timesout = new Date().getTime() - ajaxTime;
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

			students_project[seq] = projects;
		}
	})
}

function loadPythonHomework () {
	$.ajax({
		url: host + "classroom/check_folder",
		data: {
			"folder": classroom["folder"],
			"tkey": getCookie("teacher-key"),
			"student": true},
		success: function (msg) {
			files_records = msg
			files = {}
			units = new Set()
			$.each(msg, function (k, v) {
				if (k.indexOf("teacher") != -1 || k.indexOf("form") != -1) { return true; }

				cid_hwn = file_re.exec(k)[0]
				cid_hwn = cid_hwn.split("_")
				cid = cid_hwn[0]
				hwn = cid_hwn[1]
				if (hwn.indexOf(".") != -1) {
					hwn = hwn.substring(0, hwn.indexOf("."))
				}

				homework.add(hwn)
				units.add(hwn.substring(0, hwn.indexOf("-")))
				if (students_project[cid] == undefined) {
					students_project[cid] = []
					files[cid] = {}
				}
				files[cid][hwn] = k
				students_project[cid].push(hwn)
			})

			$.each(classroom["students"], function (cid, _) {
				if (students_project[cid] == undefined) {
					students_project[cid] = []
				}
			})

			units = Array.from(units).sort()
			if (units.length > 0) {
				buttonsgroup = `<br><div class="dropdown">
					<button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
					課程 <span id="lessonbtn"></span></button>
					<ul class="dropdown-menu">`
				$.each(units, function (_, i) {
					unit = i.replace("test", "課程 ")
					unit = unit.replace("hw", "功課 ")
					f = `<li style="cursor:pointer"><a onclick="changeFileUnit('{1}')">{0}</a></li>`
					buttonsgroup += format(f,
						unit,
						i)
				})
				buttonsgroup += `</ul></div><br>`
				$("#buttonsgroup").html(buttonsgroup)

				changeFileUnit(units[0])
			}
			else {
				// No file uploaded
			}
			showClassroomJob('homework')
		}
	})
}

function changeFileUnit (unit) {
	$("#lessonbtn").html(" - " + unit)
	$("#porjects")[0].innerHTML = "";
	$("#homewrok")[0].innerHTML = "";

	homeworks = Array.from(homework).sort();

	thead = "<thead><tr><th>學生 \\ 功課</th>";
	$.each(homeworks, function (_, i) {
		if (i.startsWith(unit)) {
			filename_seq = i.substring(i.indexOf("-") + 1)
			thead +=  format(PY_HW_UNIT_TB_TITLE_F,
				i,
				filename_seq)
		}
	})
	thead += "</tr></thead>";

	tbody = "<tbody>"
	$.each(students_project, function (k, v) {
		tbody += format(PY_HW_S_TB_SIDE_F,
			k,
			unit,
			classroom["students"][k]
			)

		v.sort()

		comments_keys = []
		if (classroom["comment"][k] != undefined) {
			comments_keys = Object.keys(classroom["comment"][k])
		}
		$.each(homeworks, function (_, i) {
			if (i.startsWith(unit)) {
				if (v.includes(i)) {
					if (comments_keys.includes(i)) {
						tbody += format(PY_HW_TB_F,
							"color: cornflowerblue",
							i,
							k
							)
					}
					else {
						tbody += format(PY_HW_TB_F,
							"",
							i,
							k
							)
					}
				}
				else {
					tbody += `<td></td>`
				}
			}
		})
		tbody += "</tr>"
	})
	tbody += "</tbody>"

	t = format(`<table class="table homework">{0}{1}</table>`, thead, tbody)

	$("#homewrok")[0].innerHTML = t
}

function displayPyUnit (unit) {
	f = `<button class="hwbtn" onclick="show_file('{1}','{2}','{3}')">{0}</button>`
	projects_html = $("#porjects")[0]
	projects_html.innerHTML = ""
	slide = ""

	$.each(students_project, function (s, i) {
		if (i.includes(unit)) {
			filename = i[i.indexOf(unit)]
			slide += format(f,
				classroom["students"][s],
				files[s][filename],
				filename,
				s)
		}
	})

	projects_html.innerHTML += "<h4>功課 " + unit + "</h4>"
	if (slide != "") {
		slide += "</section><br>"
		projects_html.innerHTML += slide
	}
}

function displayPyId (sid, hwstr) {
	f = `<button class="hwbtn" onclick="show_file('{1}','{2}','{3}')">{0}</button>`
	projects_html = $("#porjects")[0]
	projects_html.innerHTML = ""
	slide = ""

	$.each(students_project[sid], function (s, i) {
		if (i.startsWith(hwstr)) {
			slide += format(f,
				i.substring(i.indexOf("-") + 1),
				files[sid][i],
				i,
				sid)
		}
	})

	projects_html.innerHTML += "<h4>" + classroom["students"][sid] + " 的功課</h4>"
	if (slide != "") {
		slide += "</section><br>"
		projects_html.innerHTML += slide
	}
}

function displayScUnit (unit) {
	projects_html = $("#porjects")[0]
	projects_html.innerHTML = ""
	slide = ""

	$.each(students_project, function (s, i) {
		if (Object.keys(i).includes(unit)) {
			project_id = i[unit]
			if (slide == "") {
				slide = `<section class="regular slider scratch">`
			}
			slide += format(PICTURE_F,
				project_id,
				unit,
				classroom["students"][s][1],
				classroom["students"][s][0])
		}
	})
	projects_html.innerHTML += "<h4>功課 " + unit + "</h4>"
	if (slide != "") {
		slide += "</section><br>"
		projects_html.innerHTML += slide
	}

	setTimeout(function () {
		$(".scratch").slick({
			dots: true,
			infinite: true,
			slidesToShow: 3,
			slidesToScroll: 3
		});
	}, 300)
}

function displayScId (sid) {
	projects_html = $("#porjects")[0]
	projects_html.innerHTML = ""
	slide = ""

	$.each(students_project[sid], function (s, i) {
		if (slide == "") {
			slide = `<section class="regular slider scratch">`
		}
		slide += format(PICTURE_F,
			i,
			s,
			classroom["students"][sid][1],
			s)
	})
	projects_html.innerHTML += "<h4>" + classroom["students"][sid][0] + " 的功課</h4>"
	if (slide != "") {
		slide += "</section><br>"
		projects_html.innerHTML += slide
	}

	setTimeout(function () {
		$(".scratch").slick({
			dots: true,
			infinite: true,
			slidesToShow: 3,
			slidesToScroll: 3
		});
	}, 300)
}

function loadTeacherFiles () {
	$.ajax({
		url: host + "classroom/check_folder",
		data: {
			"folder": classroom["folder"],
			"tkey": getCookie("teacher-key")},
		success: function (msg) {
			$("#filelist")[0].innerHTML = ""
			$.each(msg, function (_, i) {
				$("#filelist")[0].innerHTML += format(
					`<li class='filelist'><a href="/downloadfile/{0}/teacher/{1}" target="_blank">{1}</a></li>`,
					classroom["folder"],
					i)
			})
		}
	})
}

function loadStudentsGrade () {
	$.ajax({
		url: host + "classroom/form",
		data: {
			"tkey": getCookie("teacher-key"),
			"folder": classroom["folder"],
			"answer": true,
			"type": classroom["type"],
		},
		success: function (msg) {
			classroom["answer"] = msg
			$.ajax({
				url: host + "classroom/form",
				data: {
					"tkey": getCookie("teacher-key"),
					"folder": classroom["folder"],
				},
				success: function (msg) {
					classroom["grade"] = msg

					forms_name = new Set()
					$.each(msg, function (_, forms) {
						$.each(forms, function (form, _) {
							if (form in classroom["answer"]) {
								forms_name.add(form)
							}
						})
					})
					forms_name = Array.from(forms_name)
					forms_name.sort()
					classroom["forms"] = forms_name

					html = ""
					$.each(forms_name, function (_, i) {
						html += format(`<li style="cursor:pointer"><a onclick="">{1}</a></li>`,
							"",
							i,
							)
					})
					
					$("#grade-form")[0].innerHTML = html
				}
			})
		}
	})
}

function showChart (method) {
	if (method == "first" || method == "finish") {
		$("#grade-detail").hide();

		data = []
		labels = []
		if (method == "first") {
			labels = ["成功", "需要繼續嘗試"]
			first_success = 0
			non_first_success = 0
			$.each(classroom["grade"], function (_, i) {
				if (chart_form in i) {
					if (i[chart_form].indexOf(classroom["answer"][chart_form]) == 0) {
						first_success += 1
					}
					else {
						non_first_success += 1
					}
				}
			})
			data = [first_success, non_first_success]
		}
		else {
			labels = ["作答過", "還沒達到"]
			answered = 0
			non_answered = 0

			length = 0
			if (typeof(classroom["students"]) == "object") {
				length = Object.keys(classroom["students"]).length
			}
			else {
				length = classroom["students"].length
			}
			non_answered += length - Object.keys(classroom["grade"]).length
			$.each(classroom["grade"], function (_, i) {
				if (i[chart_form] == undefined) {
					non_answered += 1
				}
				else {
					answered += 1
				}
			})
			data = [answered, non_answered]
		}

		if (data.length == 0) {
			$("#chart").hide()
			return
		}

		$("#chart").show()
		chart.data["datasets"][0]["data"] = data
		chart.data["labels"] = labels
		chart.data["datasets"][0]["backgroundColor"] = [
			"rgb(16, 232, 124)",
			"rgb(74, 94, 124)",
			]
		chart.update()
	}
	else if (method == "times") {
		$("#grade-detail").hide();

		times = {}
		$.each(classroom["grade"], function (_, i) {
			if (chart_form in i) {
				index = i[chart_form].indexOf(classroom["answer"][chart_form])
				if (index != -1) {
					if (times[index] == undefined) {
						times[index] = 0;
					}
					times[index] += 1;
				}
			}
		})

		labels = Object.keys(times);
		data = Object.values(times);

		if (data.length == 0) {
			$("#chart").hide();
			return
		}

		colors = []
		for (i=0;i<data.length;i++) {
			colors.push(format(
				"rgb({0}, {1}, {2})",
				Math.floor(Math.random() * 255),
				Math.floor(Math.random() * 255),
				Math.floor(Math.random() * 255),
				))
		}

		$("#chart").show()
		chart.data["datasets"][0]["data"] = data
		chart.data["labels"] = labels
		chart.data["datasets"][0]["backgroundColor"] = colors
		chart.update()
	}
	else if (method == "data") {
		$("#chart").hide();
		$("#grade-detail").show();

		form_answer = classroom["answer"][chart_form]
		form_answer = form_answer.split("a")

		// chart
		thead = "<tr><th>學生 \\ 題目</th>";
		$.each(form_answer, function (i) {
			thead +=  format(`<th>{0}</th>`,
				i + 1)
		})
		thead += "</tr>";

		tbody = ""
		
		$.each(classroom["students"], function (i, name) {
			tr = format(`<tr class="hover" onclick="showFormStudentDetail('{0}')"><td>{1}</td>`,
				i,
				name
				)
			if (classroom["grade"][i] != undefined) {
				if (classroom["grade"][i][chart_form] != undefined) {
					answers = classroom["grade"][i][chart_form];
					answers = answers[answers.length - 1];
					answers = answers.split("a")

					$.each(form_answer, function (e, right_one) {
						if (answers[e] == right_one) {
							tr += `<td><i class="fa fa-check" style="color: mediumseagreen" aria-hidden="true"></i></td>`
						}
						else {
							tr += `<td><i class="fa fa-times" style="color: tomato" aria-hidden="true"></i></td>`
						}
					})
					tr += "</tr>"
					tbody += tr
					return true;
				}
			}
			$.each(form_answer, function (_) {
				tr += "<td></td>"
			})
			tr += "</tr>"
			tbody += tr
		})

		$("#grade-detail-head")[0].innerHTML = thead
		$("#grade-detail-body")[0].innerHTML = tbody
	}
}

function showFormStudentDetail (sid) {
	$("#student-detail-name")[0].innerHTML = classroom["students"][sid]

	if (classroom["grade"][sid] == undefined) {
		$("#student-detail-head")[0].innerHTML = "<h4>此學生尚未回答問題</h4>"
		$("#student-detail-body")[0].innerHTML = ""
	}
	if (classroom["grade"][sid][chart_form] == undefined) {
		$("#student-detail-head")[0].innerHTML = "<h4>此學生尚未回答問題</h4>"
		$("#student-detail-body")[0].innerHTML = ""
	}

	thead = "<tr><th>回答次數 \\ 題目</th>";
	$.each(form_answer, function (i) {
		thead +=  format(`<th>{0}</th>`,
			i + 1)
	})
	thead += "</tr>";

	tbody = ""
	$.each(classroom["grade"][sid][chart_form], function (i, answer) {
		tr = format(`<tr class="hover"><td>{0}</td>`,
				i + 1
				)
		answers = answer.split("a")
		$.each(form_answer, function (e, right_one) {
			if (answers[e] == right_one) {
				tr += `<td><i class="fa fa-check" style="color: mediumseagreen" aria-hidden="true"></i></td>`
			}
			else {
				tr += `<td><i class="fa fa-times" style="color: tomato" aria-hidden="true"></i></td>`
			}
		})
		tr += "</tr>"
		tbody += tr
	})

	$("#student-detail-head")[0].innerHTML = thead
	$("#student-detail-body")[0].innerHTML = tbody
}

function deleteClassroom () {
	answer = prompt(format("你確定要刪除教室 '{0}'?\n如果確定請輸入教室名字", classroom["name"]))
	if (answer != classroom["name"]) {
		alert("取消刪除");
		return ;
	}
	else {
		json = {
			"tkey": getCookie("teacher-key"),
			"clsid": classroom["id"],
		}
		$.ajax({
			url: host + "classroom/?" + $.param(json),
			type: 'DELETE',
			success: function(result) {
				window.location.reload()
			}
		})
	}
}

TB_HTML_PY = `<table class="table">
	<tr>
		<th class="text-center">學生名字</th>
		<th class="text-center">Coding 4 Fun 帳號</th>
	</tr>
	<tbody id="change-student-field">
		{0}
	</tbody>
	<tr>
		<td stylle="cursor: pointer;color: cornflowerblue" onclick="newField()">
			<i class="fa fa-fw fa-plus"></i>
		</td>
	</tr>
</table>`

TBBODY_HTML_PY = `<tr>
	<td><input name="{2}" class="form-control text-center" type="text" value="{0}" /></td>
	<td><input name="{2}" class="form-control text-center" type="text" value="{1}" /></td>
</tr>`

TB_HTML_SC = `<table class="table">
	<tr>
		<th>學生名字</th>
		<th>Coding 4 Fun 帳號</th>
		<th>Scratch 帳號</th>
	</tr>
	<tbody id="change-student-field">
		{0}
	</tbody>
	<tr>
		<td stylle="cursor: pointer;color: cornflowerblue" onclick="newField()">
			<i class="fa fa-fw fa-plus"></i>
		</td>
	</tr>
</table>`

TBBODY_HTML_SC = `<tr>
	<td><input name="{3}" class="form-control text-center" type="text" value="{0}" /></td>
	<td><input name="{3}" class="form-control text-center" type="text" value="{1}" /></td>
	<td><input name="{3}" class="form-control text-center" type="text" value="{2}" /></td>
</tr>`
FIELD = `<td><input name="{0}" class="form-control text-center" type="text" placeholder="..." /></td>`

field_num = 0
field_num_2_cid = {}
field_num_2_sid = {}
wrong_field = false

function showChangeClassroom () {
	$("#change-student").modal("show")
	$("#change_classroom_name")[0].value = classroom["name"]

	seqs = {}
	json = {
		"tkey":getCookie("teacher-key")
	}
	if (classroom["type"].startsWith("python")) {
		json["ids"] = Object.keys(classroom["students"])
	}
	else {
		json["ids"] = []
		$.each(classroom["students"], function (_, i) {
			json["ids"].push(i[1])
			seqs[i[1]] = _
		})
	}

	$.ajax({
		url: host + "classroom/",
		data: json,
		success: function (msg) {
			table = ""
			if (classroom["type"].startsWith("python")) {
				tbody2 = ""
				$.each(msg, function (id, userid) {
					tbody2 += format(TBBODY_HTML_PY,
						classroom["students"][id],
						userid,
						field_num)
					field_num ++
				})
				table = format(TB_HTML_PY,
					tbody2)
			}
			else {
				tbody2 = ""
				$.each(msg, function (id, userid) {
					tbody2 += format(TBBODY_HTML_SC,
						classroom["students"][seqs[id]][0],
						userid,
						classroom["students"][seqs[id]][2],
						field_num)
					field_num ++
				})
				table = format(TB_HTML_SC,
					tbody2)
			}
			$("#change-student-table")[0].innerHTML = table
		}
	})
}

function newField () {
	html = $("<tr>")
	if (classroom["type"].startsWith("python")) {
		field = $(format(FIELD, field_num))
		html.append($(format(FIELD, field_num)))
		html.append($(format(FIELD, field_num)))
	}
	else {
		field = $(format(FIELD, field_num))
		html.append($(format(FIELD, field_num)))
		html.append($(format(FIELD, field_num)))
		html.append($(format(FIELD, field_num)))
	}
	$("#change-student-field").append(html)
	field_num ++
}

function checkChangeStudent () {
	wrong_field = false
	cids = []
	if (classroom["type"].startsWith("python")) {
		for (i=0;i<field_num;i++) {
			h = $("[name=" + i + "]")
			h[0].style.border = ""
			h[1].style.border = ""
			if (h[0].value == "" && h[1].value != "") {
				h[0].style.border = "red 2px solid"
				wrong_field = true
			}
			else if (h[0].value != "" && h[1].value == "") {
				h[1].style.border = "red 2px solid"
				wrong_field = true
			}
			if (h[1].value != "") {
				v = h[1].value
				cids.push(v)
				field_num_2_cid[v.toString()] = i
			}
		}

		$("#bg").show()
		$.ajax({
			url: host + "teacher/user",
			data: {"tkey": getCookie("teacher-key"), "users": cids},
			success: function (msg) {
				$.each(msg["none"], function (_, i) {
					h = $("[name=" + field_num_2_cid[i] + "]")
					if (h[0].value != "" || h[1].value != "") {
						h[1].style.border = "red 2px solid"
						wrong_field = true
					}
				})
				if (!wrong_field) {
					names = []
					for (i=0;i<field_num;i++) {
						h = $("[name=" + i + "]")
						if (h[0].value != "") {
							names.push(h[0].value)
						}
					}
					json = {
						"clsid": classroom["id"],
						"name": $("#change_classroom_name")[0].value,
						"students_name": names,
						"students_cid": cids,
						"students_sid": [],
						"tkey": getCookie("teacher-key")
					}
					$("#bg").hide()
					$.ajax({
						url: host + "classroom/",
						type: "PUT",
						dataType: "json",
						data: JSON.stringify(json),
						contentType: "application/json; charset=utf-8",
						success: function (msg) {
							alert("更改成功, 將自動重新整理");
							location.reload()
						},
						error: function (error) {
						}
					})
				}
			}
		})
	}
	else {
		cids = []
		sids = []
		for (i=0;i<field_num;i++) {
			h = $("[name=" + i + "]")
			h[0].style.border = ""
			h[1].style.border = ""
			h[2].style.border = ""
			if (h[0].value == "" && (h[1].value != "" || h[2].value != "")) {
				h[0].style.border = "red 2px solid"
				wrong_field = true
			}
			else if (h[0].value != "") {
				if (h[1].value == "") {
					h[1].style.border = "red 2px solid"
					wrong_field = true
				}
				if (h[2].value == "") {
					h[2].style.border = "red 2px solid"
					wrong_field = true
				}
			}
			if (h[1].value != "" && h[2].value == "") {
				h[2].style.border = "red 2px solid"
				wrong_field = true
			}
			if (h[1].value == "" && h[2].value != "") {
				h[1].style.border = "red 2px solid"
				wrong_field = true
			}

			if (h[1].value != "") {
				v = h[1].value
				cids.push(v)
				field_num_2_cid[v.toString()] = i
			}
			if (h[2].value != "") {
				v = h[2].value
				sids.push(v)
				field_num_2_sid[v.toString()] = i
			}
		}

		$("#bg").show()
		quest_id = 0
		$.each(sids, function (_, sid) {
			$.ajax({
				url: "https://scratch.mit.edu/users/" + sid,
				success: function (msg) {
					quest_id ++
					if (sids.length == quest_id) {
						$("#bg").hide()
						if (!wrong_field) {
							names = []
							for (i=0;i<field_num;i++) {
								h = $("[name=" + i + "]")
								if (h[0].value != "") {
									names.push(h[0].value)
								}
							}
							json = {
								"name": $("#change_classroom_name")[0].value,
								"clsid": classroom["id"],
								"students_name": names,
								"students_cid": cids,
								"students_sid": sids,
								"tkey": getCookie("teacher-key")
							}
							$.ajax({
								url: host + "classroom/",
								type: "PUT",
								dataType: "json",
								data: JSON.stringify(json),
								contentType: "application/json; charset=utf-8",
								success: function (msg) {
									alert("更改成功, 將自動重新整理");
									location.reload()
								},
								error: function (error) {
									console.log(error)
								}
							})
						}
					}
				},
				error: function (error) {
					quest_id ++
					h = $("[name=" + field_num_2_sid[sid] + "]")
					wrong_field = true
					if (h[0].value != "" || h[1].value != "" || h[2].value != "") {
						h[2].style.border = "red 2px solid"
						wrong_field = true
					}
					if (sids.length == quest_id) {
						$("#bg").hide()
					}
				}
			})
		})

		$.ajax({
			url: host + "teacher/user",
			data: {"tkey": getCookie("teacher-key"), "users": cids},
			success: function (msg) {
				$.each(msg["none"], function (_, i) {
					h = $("[name=" + field_num_2_cid[i] + "]")
					if (h[0].value != "" || h[1].value != "" || h[2].value != "") {
						h[1].style.border = "red 2px solid"
						wrong_field = true
					}
				})
			}
		})
	}
}

function playScratchProject (project_id, hw_s, student_id) {
	$("#project_viewer").modal("show");
	$("#copyCode").hide();
	$("#file").hide();
	$("#scratch_iframe").show();

	$("#scratch_iframe")[0].src = format(PROJECT_EMBED_F, project_id)
	$("#s_project_page")[0].href = format(PROJECT_PAGE_F, project_id)
	$("#project-title")[0].innerHTML = classroom["students"][student_id][0] + " - " + hw_s

	$("#project-comment")[0].value = ""
	if (classroom["comment"][student_id] != undefined) {
		comment = classroom["comment"][student_id][hw_s]
		if (comment != undefined) {
			$("#project-comment")[0].value = comment
		}
	}

	$("#changecomment")[0].onclick = function () {
		comment = $("#project-comment")[0].value
		if (comment.length == 0) {
			alert("不能留空");
			return;
		}
		json = {
			"tkey": getCookie("teacher-key"),
			"cls_id": classroom["id"],
			"student": student_id,
			"hw": hw_s,
			"comment": comment,
		}
		$.ajax({
			url: host + "classroom/comment",
			type: "POST",
			dataType: "json",
			data: JSON.stringify(json),
			contentType: "application/json; charset=utf-8",
			success: function (msg) {
				reloadComment(classroom["id"]);
				alert("修改成功")
			},
			error: function (error) {
				console.log(error)
			}
		})
	}
}

function parseFile (Text) {
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

function showFile (file, student_id) {
	$("#project_viewer").modal("show");
	$("#copyCode").show();
	$("#file").show();
	$("#scratch_iframe").hide();

	$("#scratch_iframe")[0].src = ""

	filepath = files[student_id][file]
	updated_time = files_records[filepath]["updated_time"]
	if (updated_time == null) { updated_time = "無紀錄" }

	lastupdate = files_records[filepath]["lastupdate"]
	if (lastupdate == null) { lastupdate = "無紀錄" }

	record = format(RECORD_F,
		updated_time,
		lastupdate,
		)
	$("#hwinfo")[0].innerHTML = record

	filname = format("{0}/{1}_{2}.py",
		classroom["folder"],
		student_id,
		file)
	$("#s_project_page")[0].href = "/downloadfile/" + filname
	$("#project-title")[0].innerHTML = classroom["students"][student_id] + " - " + file

	$("#project-comment")[0].value = ""
	if (classroom["comment"][student_id] != undefined) {
		comment = classroom["comment"][student_id][file]
		if (comment != undefined) {
			$("#project-comment")[0].value = comment
		}
	}

	$.ajax({
		url: "downloads/" + filname,
		cache: false,
		success: function (msg) {
			$("#file")[0].innerHTML = parseFile(msg)
			file_text = msg
		}
	})

	$("#changecomment")[0].onclick = function () {
		comment = $("#project-comment")[0].value
		if (comment.length == 0) {
			alert("不能留空");
			return;
		}
		json = {
			"tkey": getCookie("teacher-key"),
			"cls_id": classroom["id"],
			"student": student_id,
			"hw": file,
			"comment": comment,
		}
		$.ajax({
			url: host + "classroom/comment",
			type: "POST",
			dataType: "json",
			data: JSON.stringify(json),
			contentType: "application/json; charset=utf-8",
			success: function (msg) {
				reloadComment(classroom["id"]);
				alert("修改成功")
			},
			error: function (error) {
				console.log(error)
			}
		})
	}
}

function copyCode () {
	text = file_text
	text = text.replace(/\</g, "&lt;").replace(/\>/g, "&gt;")
	text = text.replace(/\n/g, "<br>")
	text = text.replace(/ /g, "&nbsp;")
	$("#file")[0].innerHTML = text;

	s = window.getSelection();
	r = document.createRange()
	r.selectNode($("#file")[0])
	s.removeAllRanges()
	s.addRange(r)

	document.execCommand("copy");
	s.removeAllRanges()

	$("#file")[0].innerHTML = parseFile(file_text);
}

function reloadComment (clsr_id) {
	$.ajax({
		url: host + "classroom/comment?cls_id=" + clsr_id,
		success: function (msg) {
			classrooms[clsr_id]["comment"] = msg
			classroom["comment"] = msg
		}
	})
}

function newLinksField() {
	$('#links').append($(`<input name="links" class="form-control" style="width: 80%"><br>`))
}

function saveLinks() {
	links = []
	$.each($("[name=links]"), function (_, i) {
		links.push(i.value)
	})
	json = {
		"clsid": classroom["id"],
		"links": links,
		"tkey": getCookie("teacher-key")
	}
	$.ajax({
		url: host + "classroom/",
		type: "PUT",
		dataType: "json",
		data: JSON.stringify(json),
		contentType: "application/json; charset=utf-8",
		success: function (msg) {
			alert("更改成功");
		},
		error: function (error) {
		}
	})
}

function showClassroomJob(job_type) {
	$(".clsrom-job").hide()
	$("#clsrom-" + job_type).show()

	if (job_type == "grade") {
		chart_form = classroom["forms"][0]
		showChart("first")
	}
} 
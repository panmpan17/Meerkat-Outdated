classrooms = null;
a2z = "abcdefghijklmnopqrstuvwxyz"
classroom_format = `<li id="button-classroom-{1}">
	<a onclick="changeclassroom('{1}')">{0}</a>
</li>`
classroom_main_format = `<hr />
<div class="hover" onclick="changeclassroom('{3}')">
<h4 style="color:royalblue">{0}</h4>
人數: {1}<br>
<span style="color:darkgray">開始時間:</spawn> {2}
</div>`
projects_fromat = "https://scratch.mit.edu/users/{0}/projects/"

picture_fromat = `\
<div>
	<a style="cursor: pointer" onclick="play_scratch_project('{0}', '{1}', '{2}')">
		<img src="//cdn2.scratch.mit.edu/get_image/project/{0}_144x108.png" style="border: 1px rgba(50, 50, 50, 0.5) solid;"/>
		{3}
	</a>
</div>`
project_embed_fromat = "//scratch.mit.edu/projects/embed/{0}/?autostart=false"
project_page_format = "https://scratch.mit.edu/projects/{0}/"
s_projct_match = null

file_re = RegExp("[0-9]+_.*")

SCRATCH_HW_TB_FROMAT = `<td class="hover" onclick="play_scratch_project({1}, {2}, {3})">
	<i class="fa fa-check" style="{0}" aria-hidden="true"></i>
</td>`
SC_HW_UNIT_TB_TITLE_F = `<th class="hover" onclick="displayScUnit('{0}')">
	{0}
</th>`
SC_HW_S_TB_SIDE_F = `<tr><td class="hover" onclick="displayScId('{0}')">{1}</td>`


PY_HW_TB_F = `<td class="hover" onclick="show_file('{1}', {2})">
	<i class="fa fa-check" style="{0}" aria-hidden="true"></i>
</td>`
PY_HW_UNIT_TB_TITLE_F = `<th class="hover" onclick="displayPyUnit('{0}')">
	{1}
</th>`
PY_HW_S_TB_SIDE_F = `<tr><td class="hover" onclick="displayPyId('{0}','{1}')">{2}</td>`

record_format = "上傳次數: {0}<br>更新上傳時間: {1}"

file_text = ""
files = {}
files_records = {}

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
				$("#classrooms")[0].innerHTML += format(classroom_format,
					msg[i]["name"],
					msg[i]["id"]);
				$("#classroom-main")[0].innerHTML += format(classroom_main_format,
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
	// $("#uploadfile")[0].onclick = function () {
	// 	alert("1")
	// }

	homework = new Set();
	students_project = {};
	if (classroom["type"].indexOf("scratch") != -1) {
		t_l = classroom["type"].split("_")
		s_level = a2z[t_l[1] - 1]

		timesout = 5000
		s_projct_match = RegExp("[" + s_level + s_level.toUpperCase() + "][0-9]{1,3}\-")
		$.each(classroom["students"], function (i, s) {
			loadscratchhomwork(
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
					$.each(homeworks, function (seq, i) {
						h = v[i];
						if (h != undefined) {
							if (comments_keys.includes(i)) {
								tbody += format(SCRATCH_HW_TB_FROMAT,
									"color: cornflowerblue",
									h,
									i,
									k)
							}
							else {
								tbody += format(SCRATCH_HW_TB_FROMAT,
									"",
									h,
									i,
									k)
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
		}, 100)
	}
	else if (classroom["type"].indexOf("python") != -1) {
		$("#student-num")[0].innerHTML = Object.keys(classroom["students"]).length;
		$.ajax({
			url: host + "classroom/check_folder",
			data: {
				"folder": classroom["folder"],
				"key": getCookie("key"),
				"student": true},
			success: function (msg) {
				files_records = msg
				files = {}
				units = new Set()
				console.log(msg)
				$.each(msg, function (k, v) {
					if (k.indexOf("teacher") != -1) { return true; }

					try {
						cid_hwn = file_re.exec(k)[0]
					}
					catch (e) {return true;}
					
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

				units = Array.from(units)
				units_array = []
				$.each(units, function (_, i) {
					value = i.replace("test", "").replace("hw", "")
					value = parseInt(value)
					insert_index = 0
					$.each(units_array, function (_, e) {
						e_value = parseInt(e.replace("test", "").replace("hw", ""))
						if (e_value > value) {
							return false;
						}
						insert_index += 1
					})
					units_array.splice(insert_index, 0, i)
				})
				units = units_array

				if (units.length > 0) {
					buttonsgroup = `<br><div class="dropdown">
						<button type="button" class="btn btn-default btn-lg dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
						課程 <span id="lessonbtn"></span></button>
						<ul class="dropdown-menu">`
					$.each(units, function (_, i) {
						unit = i.replace("test", "課程 ")
						unit = unit.replace("hw", "功課 ")
						f = `<li style="cursor:pointer"><a onclick="changefileunit('{1}')">{0}</a></li>`
						buttonsgroup += format(f,
							unit,
							i)
					})
					buttonsgroup += `</ul></div><br>`
					$("#buttonsgroup").html(buttonsgroup)

					changefileunit(units[0])
				}
				else {
					// No file uploaded
				}
			}
		})
	}

	// display links
	$.each(classroom["links"], function (_, i) {
		$('#links').append($(format(`<input name="links" value="{0}" class="form-control" style="width: 80%"><br>`,
			i)))
	})

	// load teacher's file
	$.ajax({
		url: host + "classroom/check_folder",
		data: {
			"folder": classroom["folder"],
			"key": getCookie("key")},
		success: function (msg) {
			$("#filelist")[0].innerHTML = ""
			$.each(msg, function (_, i) {
				$("#filelist")[0].innerHTML += format(
					`<li class='filelist'><a href="/downloadfile/{0}/teacher/{1}" target="_blank">{1}</a></li>`,
					classroom["folder"],
					i)
			})
		}})
}

function changefileunit (unit) {
	$("#lessonbtn").html(" - " + unit)
	$("#porjects")[0].innerHTML = "";
	$("#homewrok")[0].innerHTML = "";

	homeworks = Array.from(homework).sort();

	thead = "<thead><tr><th>學生 \\ 功課</th>";
	unit += "-"
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

function loadscratchhomwork (student_name, cid, student_id, seq) {
	var ajaxTime = new Date().getTime();
	$.ajax({
		url: format(projects_fromat, student_id),
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
			slide += format(picture_fromat,
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
		slide += format(picture_fromat,
			i,
			s,
			sid,
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

function delete_classroom () {
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
		<td stylle="cursor: pointer;color: cornflowerblue" onclick="new_field()">
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
		<td stylle="cursor: pointer;color: cornflowerblue" onclick="new_field()">
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

function show_change_classroom () {
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
			field_num = 0
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

function new_field () {
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

function check_change_student () {
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
				else {
					$("#bg").hide()
				}
			},
			error: function (error) {console.log(error)}
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

function play_scratch_project (project_id, hw_s, student_seq) {
	$("#project_viewer").modal("show");
	$("#copycode").hide();
	$("#file").hide();
	$("#scratch_iframe").show();

	$("#scratch_iframe")[0].src = format(project_embed_fromat, project_id)
	$("#s_project_page")[0].href = format(project_page_format, project_id)
	$("#project-title")[0].innerHTML = classroom["students"][student_seq][0] + " - " + hw_s
	student_id = classroom["students"][student_seq][1]

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
				reloadcomment(classroom["id"]);
				alert("修改成功")
			},
			error: function (error) {
				console.log(error)
			}
		})
	}
}

function parse_file (Text) {
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

function show_file (file, student_id) {
	$("#project_viewer").modal("show");
	$("#copycode").show();
	$("#file").show();
	$("#scratch_iframe").hide();

	$("#scratch_iframe")[0].src = ""

	filepath = files[student_id][file]
	updated_time = files_records[filepath]["updated_time"]
	if (updated_time == null) { updated_time = "無紀錄" }

	lastupdate = files_records[filepath]["lastupdate"]
	if (lastupdate == null) { lastupdate = "無紀錄" }

	record = format(record_format,
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
			$("#file")[0].innerHTML = parse_file(msg)
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
				reloadcomment(classroom["id"]);
				alert("修改成功")
			},
			error: function (error) {
				console.log(error)
			}
		})
	}
}

function copycode () {
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

	$("#file")[0].innerHTML = parse_file(file_text);
}

function reloadcomment (clsr_id) {
	$.ajax({
		url: host + "classroom/comment?cls_id=" + clsr_id,
		success: function (msg) {
			classrooms[clsr_id]["comment"] = msg
			classroom["comment"] = msg
		}
	})
}

function new_links_field() {
	$('#links').append($(`<input name="links" class="form-control" style="width: 80%"><br>`))
}

function save_links() {
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
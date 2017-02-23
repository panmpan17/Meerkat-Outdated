classrooms = null;
a2z = "abcdefghijklmnopqrstuvwxyz"
classroom_format = `<li id="button-classroom-{1}">
	<a onclick="changeclassroom('{1}')">{0}</a>
</li>`
projects_fromat = "https://scratch.mit.edu/users/{0}/projects/"

picture_fromat = `\
<div>
	<a style="cursor: pointer" onclick="play_scratch_project('{0}')">
		<img src="//cdn2.scratch.mit.edu/get_image/project/{0}_144x108.png" style="border: 1px rgba(50, 50, 50, 0.5) solid;"/>
		{1}
	</a>
</div>`
project_embed_fromat = "//scratch.mit.edu/projects/embed/{0}/?autostart=false"
project_page_format = "https://scratch.mit.edu/projects/{0}/"
s_projct_match = null

file_re = RegExp("[0-9]+_[0-9]+")

p_p_f = `\
<div>
	<a style="cursor: pointer" onclick="show_file('/downloads/{1}/{2}')">
		<img src="http://placehold.it/144x108/366f9e/fed958/?text={0}" style="border: 1px rgba(50, 50, 50, 0.5) solid;"/>
	</a>
</div>
`

function loadallclassroom() {
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
				classrooms[msg[i]["id"]] = msg[i]
			}
		}
	})
}

function changeclassroom(cls_id) {
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
	$("#refreshclassroom")[0].onclick = function () {
		changeclassroom(cls_id);
	}

	homework = new Set();
	students_project = {};
	if (classroom["type"].indexOf("scratch") != -1) {
		t_l = classroom["type"].split("_")
		s_level = a2z[t_l[1] - 1]

		s_projct_match = RegExp("[" + s_level + s_level.toUpperCase() + "][0-9]{1,3}\-")
		$.each(classroom["students"], function (i) {
			loadscratchhomwork(
				classroom["students"][i][2],
				classroom["students"][i][0])
		})

		setTimeout(function () {
			$(".scratch").slick({
				dots: true,
				infinite: true,
				slidesToShow: 3,
				slidesToScroll: 3
			});
			homework = Array.from(homework).sort();

			thead = "<thead><tr><th>學生 \\ 功課</th>";
			$.each(homework, function (i) {
				thead += "<th>" + homework[i] + "</th>"
			})
			thead += "</tr></thead>";

			tbody = "<tbody>"
			$.each(students_project, function (k,v) {
				tbody += "<tr><td>" + k + "</td>"

				$.each(homework, function (i) {
					h = v[homework[i]];
					if (h != undefined) {
						tbody += `<td><i class="fa fa-check" aria-hidden="true"></i></td>`
					}
					else {
						tbody += `<td></td>`
					}
				})

				tbody += "</tr>"
			})
			tbody += "</tbody>"

			t = format(`<table class="table homework">{0}{1}</table>`, thead, tbody)
			// console.log(tbody)
			// console.log(t)
			$("#homewrok")[0].innerHTML = t
		}, (600 * classroom["students"].length));
	}
	else if (classroom["type"].indexOf("python") != -1) {
		$.ajax({
			url: host + "classroom/check_folder",
			data: {"folder": classroom["folder"]},
			success: function (msg) {
				files = {}
				$.each(msg, function (i) {
					cid_hwn = file_re.exec(msg[i])[0]
					cid_hwn = cid_hwn.split("_")
					cid = cid_hwn[0]
					hwn = cid_hwn[1]

					homework.add(hwn)
					if (students_project[cid] == undefined) {
						students_project[cid] = []
						files[cid] = {}
					}
					files[cid][hwn] = msg[i]
					students_project[cid].push(hwn)
				})

				$.each(classroom["students"], function (cid, _) {
					if (students_project[cid] == undefined) {
						students_project[cid] = []
					}
				})

				homework = Array.from(homework).sort();

				thead = "<thead><tr><th>學生 \\ 功課</th>";
				$.each(homework, function (i) {
					thead += "<th>" + homework[i] + "</th>"
				})
				thead += "</tr></thead>";

				tbody = "<tbody>"
				$.each(students_project, function (k,v) {
					tbody += "<tr><td>" + classroom["students"][k] + "</td>"

					v.sort()
					$.each(homework, function (i) {
						h = v.indexOf(homework[i])
						if (h != -1) {
							tbody += `<td><i class="fa fa-check" aria-hidden="true"></i></td>`
						}
						else {
							tbody += `<td></td>`
						}
					})

					projects_html = $("#porjects")[0]
					slide = ""
					$.each(v, function (i) {
						if (slide == "") {
							slide = `<section class="regular slider python">`
						}
						slide += format(p_p_f,
							v[i],
							classroom["folder"],
							files[k][v[i]])
					})
					projects_html.innerHTML += "<h4>" + classroom["students"][k] + "</h4>"

					if (slide != "") {
						slide += "</section><br>"
						projects_html.innerHTML += slide
					}
					tbody += "</tr>"
				})
				tbody += "</tbody>"

				t = format(`<table class="table homework">{0}{1}</table>`, thead, tbody)

				$("#homewrok")[0].innerHTML = t

				setTimeout(function () {
					$(".python").slick({
						dots: true,
						infinite: true,
						slidesToShow: 4,
						slidesToScroll: 4
					});
				}, 100);
			}
		})
		
	}
}

function loadscratchhomwork(student_id, student_name) {
	$.ajax({
		url: format(projects_fromat, student_id),
		success: function (msg) {
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
			projects_html = $("#porjects")[0]
			slide = ""
			p = Object.keys(projects).sort()
			$.each(p, function (i) {
				if (slide == "") {
					slide = `<section class="regular slider scratch">`
				}
				slide += format(picture_fromat,
					projects[p[i]],
					p[i])
			})
			projects_html.innerHTML += format(`<h4>{0} ({1})</h4>`,
				student_name,
				student_id)
			if (slide != "") {
				slide += "</section><br>"
				projects_html.innerHTML += slide
			}

			students_project[student_name] = projects;
		}
	})
}

function play_scratch_project(project_id) {
	$("#scratch_project").show();
	$("#scratch_iframe")[0].src = format(project_embed_fromat, project_id)

	$("#s_project_page")[0].href = format(project_page_format, project_id)
}

function show_file(file) {
	$("#scratch_project").show();
	$("#scratch_iframe")[0].src = file

	$("#s_project_page")[0].href = file
}
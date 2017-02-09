classrooms = null;
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
s_projct_match = null
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
	$("#classroom-type")[0].innerHTML = CLASS_TO[classroom["type"]]

	$("#porjects")[0].innerHTML = "";
	if (classroom["type"].indexOf("scratch") != -1) {
		t_l = classroom["type"].split("_")
		s_level = a2z[t_l[1] - 1]

		homework = new Set();
		s_projct_match = RegExp("[" + s_level + s_level.toUpperCase() + "][0-9]{1,3}\-")
		$.each(classroom["students"], function (i) {
			loadscratchhomwork(classroom["students"][i][2])
		})

		setTimeout(function () {
			$(".scratch").slick({
				dots: true,
				infinite: true,
				slidesToShow: 3,
				slidesToScroll: 3
			});
			console.log(Array.from(homework).sort())
		}, (600 * classroom["students"].length));
	}
}

function loadscratchhomwork(student_id) {
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
				slide += format(picture_fromat, projects[p[i]], p[i])
			})
			projects_html.innerHTML += "<h4>" + student_id + "</h4>" 
			if (slide != "") {
				slide += "</section><br>"
				projects_html.innerHTML += slide
			}
		}
	})
}

function play_scratch_project(project_id) {
	$("#scratch_project").show();
	$("#scratch_iframe")[0].src = format(project_embed_fromat, project_id)
}
loadallclassroom();
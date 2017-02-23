// this one check user's userid password
id_pass_re = new RegExp("[a-zA-Z0-9@\.]{8,16}");
file_re = new RegExp("[0-9]+_[0-9]+")
email_re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;

a2z = "abcdefghijklmnopqrstuvwxyz"
classroom_homwork_format = `
<div class="classroom-card">
<b>{0}</b>
{3}
<div class="close" style="padding-right:10px; color: gray" onclick="howtoupload('{1}')">
	如何繳交作業
</div>
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

python_upload_html = `
<div class="close" style="padding-right:10px; color:blue">
	<label for="pythonhomework">交作業</label>
	<form enctype="multipart/form-data" action="rest/1/upload/homework" method="post" id="homeworkupload" hidden>
		<input name="homwork" id="pythonhomework" type="file" onchange="upload()"/>
		<input name="session" type="text" />
		<input name="type" type="text" value="python_01"/>
		<input name="clsroomid" type="text" value="{0}"/>
		<input name="key" type="text"/>
	</form>
</div>
`

p_p_f = `\
<div>
	<a style="cursor: pointer" onclick="show_file('/downloads/{1}/{2}')">
		<img src="http://placehold.it/144x108/366f9e/fed958/?text={0}" style="border: 1px rgba(50, 50, 50, 0.5) solid;"/>
	</a>
</div>
`

picture_fromat = `\
<div>
	<a style="cursor: pointer" onclick="play_scratch_project('{0}')">
		<img src="//cdn2.scratch.mit.edu/get_image/project/{0}_144x108.png" style="border: 1px rgba(50, 50, 50, 0.5) solid;"/>
	</a>
</div>`

project_embed_fromat = "//scratch.mit.edu/projects/embed/{0}/?autostart=false"

function matchRE(r, text) {
	match = r.exec(text);
	if (match == null) {
		return false;
	}
	if (match[0] != text) {
		return false;
	}
	return true;
}

function presslogo() {
	cookie = getCookie("id");
	if (cookie == "") {
		show("login-frame");
	}
	else {
		// dropdown menu
		toggle("accountmenu");
	}
}

function login() {
	errormsg = $("#login-errormsg")[0]

	userid = $("[name=login-userid]")[0].value;
	password = $("[name=login-password]")[0].value;
	password = sha256(password);
	if (userid && password) {
		json = {"userid":userid, "password":password}
		$.ajax({
			url: host + "logon/",
			type: "GET",
			data: json,
			success: function (msg) {
				storeCookie("id", msg["lastrowid"]);
				storeCookie("userid", msg["userid"]);
				storeCookie("key", msg["key"]);
				location.reload();
			},
			error: function (error) {
				errormsg = $("#login-errormsg")[0]
				p1 = error.responseText.indexOf("<p>") + 3
				errortype = error.responseText.substring(p1, error.responseText.indexOf("</p>", p1))
				if (errortype == "Username or password wrong") {
					errormsg.innerHTML = "帳號密碼不正確";
				}
				else if (errortype.indexOf("disable") > -1) {
					errormsg.innerHTML = "帳號已被封鎖"
				}
				return
			}
		})
	}
	else {
		errormsg.innerHTML = "請不要留空白"
		show("login-errormsg");
		return 
	}
}

function signup(){
	errormsg = $("#signup-errormsg")[0]

	userid = $("[name=signup-userid]")[0].value;
	password = $("[name=signup-password]")[0].value;
	repassword = $("[name=signup-repassword]")[0].value;
	email = $("[name=signup-email]")[0].value;
	birth = $("[name=signup-birth_year]")[0].value;
	nickname = $("[name=signup-nickname]")[0].value;
	job = $("[name=signup-job]")[0].value;

	human = grecaptcha.getResponse()

	// check every things is not empty and valid
	if (userid && password && repassword && email && birth && nickname) {
		id_valid = matchRE(id_pass_re, userid);
		pass_valid = matchRE(id_pass_re, password);
		email_valid = matchRE(email_re, email);
		if (!id_valid) {
			errormsg.innerHTML = "帳號並不符合格式";
			return
		}
		if (!pass_valid) {
			errormsg.innerHTML = "密碼並不符合格式";
			return
		}
		if (!email_valid) {
			errormsg.innerHTML = "Email 並不正確";
			return
		}
	}
	else {
		errormsg.innerHTML = "請不要留空白";
		return
	}

	password = sha256(password);
	repassword = sha256(repassword);
	if (password != repassword) {
		errormsg.innerHTML = "請確定密碼一致"
		return 
	}

	json = {
		"userid":userid,
		"password":password,
		"email":email,
		"birth_year":birth,
		"nickname":nickname,
	}

	if (job) {
		json["job"] = job;
	}

	$.ajax({
		url: host + "user/",
		type: "POST",
		dataType: "json",
		data: JSON.stringify({"recapcha": human, users: [json]}),
		contentType: "application/json; charset=utf-8",
		success: function (msg) {
			storeCookie("id", msg["lastrowid"]);
			storeCookie("userid", msg["userid"]);
			storeCookie("key", msg["key"]);
			location.reload();
		},
		error: function (error) {
			errormsg = $("#signup-errormsg")[0]
			p1 = error.responseText.indexOf("<p>") + 3
			errortype = error.responseText.substring(p1, error.responseText.indexOf("</p>", p1))
			console.log(errortype)
			if (errortype == "This userid repeat") {
				errormsg.innerHTML = "帳號重複";
			}
			else if (errortype == "You are not human") {
				errormsg.innerHTML = "請做好人類認證";
			}
			return 
		}
	})
}

function logout() {
	deleteCookie("id");
	deleteCookie("userid");
	deleteCookie("key");
	location.reload();
}

function to_html(dict) {
	$("#info-userid")[0].innerHTML = dict["userid"];
	$("#info-point")[0].innerHTML = dict["point"];
	$("#info-nick")[0].innerHTML = dict["nickname"];
	$("#info-email")[0].innerHTML = dict["email"];
	$("#info-birth")[0].innerHTML = dict["birth_year"];
	$("#info-job")[0].innerHTML = dict["job"];

	$("#info-level")[0].innerHTML = "一般";
	point = dict["point"];
	if (point > 200) {$("#info-level")[0].innerHTML = "鑽石"}
	else if (point > 100) {$("#info-level")[0].innerHTML = "白金"}
	else if (point > 20) {$("#info-level")[0].innerHTML = "黃金"}

	if (dict["active"]) {
        try {
            $("#userinfo")[0].childNodes[1].removeChild(
				$("#info-active")[0])
        }
        catch(err) {}
	}

	if (!dict["admin"]) {
        try {
			$("#userinfo")[0].childNodes[1].removeChild(
				$("#info-admin")[0])
        }
        catch(err) {}
	}
}

function showinfo() {
	hide('accountmenu');

	key = getCookie("key");
	id = getCookie("id");
	string_param = {"key":key, "id":id}
	$.ajax({
		url: host + "user/",
		type: "GET",
		data: string_param,
		success: function (msg) {
			to_html(msg);
			show('info-frame');
		},
		error: function (msg) {
			console.log(msg)
			reload = confirm("請重新登錄");
			if (reload) {
				hide('info-frame');
				show("login-frame");
			}
		}
	})
}


function resentmail() {
	$.ajax({
		url: host + "user/emailvalid",
		type: "POST",
		dataType: "json",
		data: JSON.stringify({"key": getCookie("key")}),
		contentType: "application/json; charset=utf-8",
		success: function (msg) {
			alert("請檢查 Email!!");
		},
		error: function (msg) {
			reload = confirm("請重新登錄");
			if (reload) {
				hide('info-frame');
				show("login-frame");
			}
		}

	})
}

function changepassword() {
	password = $("#change_password")[0].value
	newpassword = $("#change_newpassword")[0].value
	check_password = $("#change_check_password")[0].value

	if (!(password && newpassword && check_password)) {
		alert("不能留空");
		return;
	}
	if (password == newpassword) {
		alert("密碼沒有改變");
		return;
	}
	if (newpassword != check_password) {
		alert("請確定密碼一致");
		return;
	}

	pass_valid = matchRE(id_pass_re, newpassword);
	password = sha256(password);
	newpassword = sha256(newpassword);

	if (!pass_valid) {
		alert("密碼並不符合格式");
		return;
	}
	json = {
		"key": getCookie("key"),
		"password": password,
		"newpassword": newpassword,
	}
	$.ajax({
		url: host + "user/password",
		type: "PUT",
		dataType: "json",
		data: JSON.stringify(json),
		contentType: "application/json; charset=utf-8",
		success: function (msg) {
			alert("密碼已改變, 請重新登錄");
			hide('info-frame');
			show("login-frame");
		},
		error: function (error) {
			p1 = error.responseText.indexOf("<p>") + 3
			errortype = error.responseText.substring(p1, error.responseText.indexOf("</p>", p1))
			if (errortype == "Username or password wrong") {
				alert("密碼不正確");
				return;
			}
		}
	})
}

function showclassroom() {
	hide('accountmenu');

	$.ajax({
		url: host + "classroom/",
		type: "GET",
		data: {"key": getCookie("key")},
		success: function (msg) {
			show("classroom-frame");
			homework_html = $("#classroom-homework")[0]
			homework_html.innerHTML = "<br>";

			$.each(msg, function (i) {
				name = msg[i]["name"]
				if (msg[i]["type"].indexOf("scratch") != -1) {
					t_l = msg[i]["type"].split("_")
					s_level = a2z[t_l[1] - 1]
					s_projct_match = RegExp("[" + s_level + s_level.toUpperCase() + "][0-9]{1,3}\-")
					name += " (" + s_level.toUpperCase() + ")"

					loadscratchhomwork(msg[i]["student_cid"], msg[i]["id"])
				}

				html = ""
				if (msg[i]["type"] == 'python_01') {
					html = format(python_upload_html, msg[i]["id"])

					loadfilehomework(msg[i]["folder"], msg[i]["id"])
				}
				homework_html.innerHTML += format(
					classroom_homwork_format,
					name,
					msg[i]["type"],
					msg[i]["id"],
					html)
			})
			
		},
		error: function (msg) {
			reload = confirm("請重新登錄");
			if (reload) {
				hide('classroom-frame');
				show("login-frame");
			}
		}
	})
}

function loadscratchhomwork(student_id, clsr_id) {
	$.ajax({
		url: "https://scratch.mit.edu/users/" + student_id + "/projects/",
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

			thead = "<th>" + student_id + "</th>"
			tbody = "<td></td>"
			slide = ""
			$.each(homework, function (i) {
				if (slide == "") {
					slide = `<section class="regular slider" id="s{0}">`
				}
				slide += format(picture_fromat,
					projects[homework[i]])
				thead += "<th>" + homework[i] + "</th>";
				tbody += `<td style="font-size: 15px"><i class="fa fa-check" aria-hidden="true"></i></td>`
			})
			if (slide != "") {
				slide += "</section><br>"
			}

			$("#thead-" + clsr_id)[0].innerHTML = thead
			$("#tbody-" + clsr_id)[0].innerHTML = tbody
			$("#homeworkshelf-" + clsr_id)[0].innerHTML = format(slide, clsr_id)

			setTimeout(function () {
				$("#s" + clsr_id).slick({
					dots: true,
					infinite: true,
					slidesToShow: 3,
					slidesToScroll: 3
				});
			}, 100);
		}
	})
}

function loadfilehomework(folder, clsr_id) {
	$.ajax({
		url: host + "classroom/check_folder",
		data: {"folder": folder,
			"cid": getCookie("id")},
		success: function (msg) {
			homework = new Set()
			projects = []
			files = {}

			$.each(msg, function (i) {
				cid_hwn = file_re.exec(msg[i])[0]
				cid_hwn = cid_hwn.split("_")
				cid = cid_hwn[0]
				hwn = cid_hwn[1]

				homework.add(hwn)

				files[hwn] = msg[i]
				projects.push(hwn)
			})

			homework = Array.from(homework).sort();

			thead = "<thead><tr>";
			tbody = "<tbody><tr>"
			slide = ""
			$.each(homework, function (i) {
				if (slide == "") {
					slide = `<section style="clear: both; padding:10px;">`
				}
				slide += format(`<div style="display: inline-block;background: #366f9e;width: 100px;border-radius: 10px;\
					padding: 5px;text-align: center;color: #fed958;margin: 5px;cursor: pointer"\
					onclick="show_file('/downloads/{1}/{2}')">{0}</div>`,
					homework[i],
					folder,
					files[homework[i]])
				thead += "<th>" + homework[i] + "</th>"
				tbody += `<td style="font-size: 15px"><i class="fa fa-check" aria-hidden="true"></i></td>`
			})
			if (slide != "") {
				slide += "</section><br>"
			}

			thead += "</tr></thead>";
			tbody += "</tr></tbody>"

			$("#thead-" + clsr_id)[0].innerHTML = thead
			$("#tbody-" + clsr_id)[0].innerHTML = tbody
			$("#homeworkshelf-" + clsr_id)[0].innerHTML = slide
		}
	})
}

function howtoupload(type) {
	hide('classroom-frame');
	show('howuploadhomework-frame');

	$(".howtoupload").hide()
	$("#howtoupload-" + type).show()
}

function upload() {
	lesson = null
	while (!lesson) {
		lesson = prompt("第幾課的功課? (數字)")
		if (lesson == null) {
			return;
		}
		lesson = parseInt(lesson)
	}
	$("[name=session]")[0].value = lesson
	$("[name=key]")[0].value = getCookie("key")
	$("#homeworkupload")[0].submit()
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
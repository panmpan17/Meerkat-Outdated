var question_id = null;
var filter = {}

// 
// ASK QUESTION
//
function openask() {
	if (getCookie("id")) {
		show("ask-frame");
	}
	else {
		toggle("notlogin-frame");
	}
}

// 
// CHANGE QUESTION TYPE
// 
var q_type = 0;
var select_type = "all";
var select_values = null;
var q_text = document.getElementById("dropdownMenu1");
var q_typelist = [
	"Scratch",
	"Python",
	"Other",
]
function changetype(type) {
	q_type = type;
	q_text.innerHTML = q_typelist[type];
}

function changefilename(filename) {
	l = filename.split(".")
	return l[l.length - 1]
}

changetype(0);

// 
// CHANGE QUESTION INTO HTML
// 
var link_fmt = `<a href="{0}" target="_blank">{1}</a>`

function turn_url(string) {
	t_s_s = string.indexOf("[#")
	while (t_s_s > -1) {
		t_s_e = string.indexOf("#]", t_s_s + 2)
		t_l_e = string.indexOf("#}", t_s_e + 2)
		if ((t_s_e == -1) || (t_l_e == -1)) {break;}

		text = string.substring(t_s_s + 2, t_s_e)
		url = string.substring(t_s_e + 2, t_l_e).replace(/ /g, "")

		link = format(link_fmt, url.substring(2), text)
		if (link == "<a href=\"\"></a>") {
			t_s_s = string.indexOf("[#", t_l_e + 2)
			continue;
		}

		string = string.replace(string.substring(t_s_s, t_l_e+2), link)

		t_s_s = string.indexOf("[#")
	}
	return string;
}

page_limit = 0
page = 1
function changepage(p) {
	if (p == page) {
		return ;
	}
	if (p <= page_limit) {
		page = p;
		getallquestion(select_type, select_values);
	}
}

function prevpage () {
	if ((page - 1) >= 1) {
		changepage(page - 1)
	}
}

function nextpage () {
	if ((page + 1) <= page_limit) {
		changepage(page + 1)
	}
}

function to_questions(l) {
	// paging html
	len_pages = l["pages"]
	page_f = "<li class=\"paging{1}\" onclick=\"changepage({0})\"><a>{0}</a></li>"

	paging = `
	<nav>
		<ul class="pagination">
			<li class="paging{0}" onclick="prevpage()">
				<a aria-label="Previous">&laquo;</a>
			</li>
	`

	if (page == 1) {
		paging = format(paging, " disabled")
	}
	else {
		paging = format(paging, "")
	}

	for (i = 1; i <= len_pages; i++) {
		if (page == i) {
			paging += format(page_f, i, " press");
			continue
		}
		paging += format(page_f, i, "");
	}

	paging += `
			<li class="paging{0}" onclick="nextpage()">
				<a aria-label="Next">&raquo;</a>
			</li>
		</ul>
	</nav>
	<br>`

	if (page == len_pages) {
		paging = format(paging, " disabled")
	}
	else {
		paging = format(paging, "")
	}

	card_format = `
	<div class="card" onclick="openquestion({4})">
		<br />&nbsp;&nbsp;&nbsp;&nbsp;
		<span id="card-solved" style="background-color:{3}"><span id="card-title">{0}</span></span>
		
		<br />
		<span id="card-time">{1}</span>
		&nbsp;&nbsp;&nbsp;
		<span id="card-type" style="background-color:{5}">{2}</span>
	</div>
	<br /><br />
	`
	
	cards = "<center>";
	cards += paging
	if (l["pages"] > 0) {

		questions = l["questions"]
		for (i=0;i<questions.length;i++) {
			// 0: title, 1:time, 2:type color, 3:solved color, 4:question id
			solved_color = "Crimson" // unsolved
			if (questions[i]["solved"]) {
				solved_color = "LimeGreen";
			}

			colormatch = [
				"#ffa31a",
				"#0066cc",
				]

			card = format(card_format, questions[i]["title"],
				questions[i]["create_at"], 
				q_typelist[questions[i]["type"]],
				solved_color, questions[i]["id"], colormatch[questions[i]["type"]])

			cards += card;
		}
		cards += paging
		cards += "</center>"
	}

	else {
		cards = `
		<br />
		<br />
		<center>
			<div class="well well-lg" style="width:90%">
				沒有這類的問題
			</div>
		</center>
		`
	}

	document.getElementById("cards").innerHTML = cards;
}
// 
// SHOW SIGNLE QUESTION
// 
function getanswer(qid) {
	string_param = {"qid": qid}
	$.ajax({
		url: host + "answer/",
		type: "GET",
		data: string_param,
		success: function (msg) {
			answer_format = `<hr />
			<span id="writer"> {1} </span> <sup id="time"> {2} </sup><br />
			<div style="padding-left:30px">
				{0}
			</div>
			`

			answers = ""
			for (i=0;i<msg["answers"].length;i++) {
				m = msg["answers"][i]
				answers += format(answer_format, m["content"].replace(/\n/g, "<br>"),
					m["writer"], m["create_at"]);

				file_format = '<a target="_blank" class="file-link" download href="{0}">- 檔案 {1} - {2} </a><br>'

				file_display = "<div style=\"padding-left:30px\">"
				if (m["file1"] != "") {
					file_display += format(file_format, m["file1"], "1", changefilename(m["file1"]))
					if (m["file2"] != "") {
						file_display += format(file_format, m["file2"], "2", changefilename(m["file2"]))
						if (m["file3"] != "") {
							file_display += format(file_format, m["file3"], "3", changefilename(m["file3"]))
						}
					}
					answers += file_display + "</div></div>";
				}

			}
			answers += "<hr>"
			document.getElementById("answers").innerHTML = answers;
		},
		error: function (msg) {
			document.getElementById("answers").innerHTML = "<hr /> 目前沒有解答 <hr />";
			// NO ANSWER
		}
	})
}

function showquestion(qid) {
	string_param = {"id":qid}
	$.ajax({
		url: host + "question/",
		type: "GET",
		data: string_param,
		success: function (msg) {
			document.getElementById("answer-content").value = "";
			document.getElementById("content").innerHTML = msg["content"].replace(/\n/g, "<br>");
			document.getElementById("type").innerHTML = q_typelist[msg["type"]];

			a = "<div id=\"solved\" style=\"background-color:"
			if (msg["solved"]) {
					a += "LimeGreen";
			}
			else {
					a += "Crimson";
			}
			a += "\"></div> " + msg["title"];
			document.getElementById("title").innerHTML = a;
			document.getElementById("create_at").innerHTML = msg["create_at"];
			document.getElementById("question-writer").innerHTML = msg["writer"];
			
			if (getCookie("id") != msg["writer_id"]) {
				document.getElementById("closequestion").disabled = true;
				document.getElementById("closequestion").onclick = null;
			}
			else {
				document.getElementById("closequestion").disabled = false;
				if (msg["solved"]) {
					document.getElementById("closequestion").onclick = function () {closequestion("False")};
					document.getElementById("closequestion").innerHTML = "開啟問題";
				}
				else {
					document.getElementById("closequestion").onclick = function () {closequestion("True")};
					document.getElementById("closequestion").innerHTML = "關閉問題";
				}
			}
			if (msg["solved"]) {
				hide("answer-div")
			}
			else {
				show("answer-div")
			}
			
			file_format = '<a target="_blank" class="file-link" download href="{0}">- 檔案 {1} - {2} </a><br>'

			file_display = ""
			if (msg["file1"] != "") {
				file_display += format(file_format, msg["file1"], "1", changefilename(msg["file1"]))
				if (msg["file2"] != "") {
					file_display += format(file_format, msg["file2"], "2", changefilename(msg["file2"]))
					if (msg["file3"] != "") {
						file_display += format(file_format, msg["file3"], "3", changefilename(msg["file3"]))
					}
				}
				document.getElementById("files").innerHTML = file_display;
			}
			else {
				document.getElementById("files").innerHTML = "沒有檔案";
			}

			getanswer(qid);
			question_id = qid;
		}
	})
}

function openquestion (id) {
	show("question-frame");
	showquestion(id);
}
// 
// REST
//
function closequestion (v) {
	key = getCookie("key"),
	json = {
		"key": key,
		"qid": question_id,
		"solved": v,
	}
	$.ajax({
		url: host + "question/",
		type: "PUT",
		dataType: "json",
		data: JSON.stringify(json),
		contentType: "application/json; charset=utf-8",
		success: function (msg) {
			showquestion(question_id);
			getallquestion(select_type, select_values);
		},
		error: function (msg) {
			reload = confirm("請重新登錄");
			if (reload) {
				hide('question-frame');
				show("login-frame");
			}
		}
	})
}

function answer() {
	content = document.getElementById("answer-content").value;

	if (content) {
		key = getCookie("key");
		uid = getCookie("id");
		json = {
			"content": content,
			"writer": uid,
			"answer_to": question_id,
		}
		$.ajax({
			url: host + "answer/",
			type: "POST",
			dataType: "json",
			data: JSON.stringify({key: key,answer_json: json}),
			contentType: "application/json; charset=utf-8",
			success: function (msg) {
				f1 = document.getElementById("f1-a").files[0]
				f2 = document.getElementById("f2-a").files[0]
				f3 = document.getElementById("f3-a").files[0]
				if ((f1 != undefined) || (f2 != undefined) || (f3 != undefined)) {
					document.getElementById("answerkey").value = msg["answer_id"]
					document.getElementById("answerform").submit()
				}
				else {
					document.getElementsByName("ask-content").value = "";
					showquestion(question_id)
				}
			},
			error: function (msg) {
				reload = confirm("請重新登錄");
				if (reload) {
					hide('question-frame');
					show("login-frame");
				}
			}
		})
	}
	else {
		alert("請不要留空")
	}
}

function ask() {
	errormsg = document.getElementById("ask-errormsg");

	title = document.getElementById("ask-title").value
	content = document.getElementById("ask-content").value;
	if (title && content) {
		key = getCookie("key");
		uid = getCookie("id");
		json = {
			"title": title,
			"content": content,
			"type": q_type,
			"writer": uid,
		}
		$.ajax({
			url: host + "question/",
			type: "POST",
			dataType: "json",
			data: JSON.stringify({key: key,question_json: json}),
			contentType: "application/json; charset=utf-8",
			success: function (msg) {
				f1 = document.getElementById("f1-q").files[0]
				f2 = document.getElementById("f2-q").files[0]
				f3 = document.getElementById("f3-q").files[0]
				if ((f1 != undefined) || (f2 != undefined) || (f3 != undefined)) {
					document.getElementById("questionkey").value = msg["question_id"]
					document.getElementById("questionform").submit()
				}
				else {
					document.getElementById("ask-title").value = "";
					document.getElementById("ask-content").value = "";
					hide("ask-frame")
					openquestion(msg["question_id"])
					getallquestion(select_type, select_values)
				}
			},
			error: function (msg) {
				reload = confirm("請重新登錄");
				if (reload) {
					hide('ask-frame');
					show("login-frame");
				}
			}
		})
	}
	else {
		alert("請不要留空")
	}
}

function getallquestion(t, v) {

	if (((t == "writer") || (t == "answer")) && (v == "")) {
		reload = confirm("請登錄");
		if (reload) {
			show("login-frame");
		}
		return null;
	}

	select_values = v
	if (select_values == "True") {
		document.getElementsByClassName("active")[0].classList.remove("active");
		document.getElementById("solved").classList.add("active")
	}
	if (select_values == "False") {
		document.getElementsByClassName("active")[0].classList.remove("active");
		document.getElementById("unsolved").classList.add("active")
	}

	if (select_type != t) {
		page = 1;
		select_type = t;

		if ((t != "solved") && (t != "answer")) {
			document.getElementsByClassName("active")[0].classList.remove("active");
			document.getElementById(t).classList.add("active")
		}
	}

	document.getElementById("cards").innerHTML = '<span style="font-size:48px;color:#aaa">請稍等</span>';
	string_param = {"page": page - 1}
	string_param[t] = select_values
	$.ajax({
		url: host + "question/",
		type: "GET",
		data: jQuery.extend(string_param, filter),
		success: function (msg) {
			to_questions(msg);
			page_limit = msg["pages"]

			if (t == "answer") {
				document.getElementsByClassName("active")[0].classList.remove("active");
				document.getElementById(t).classList.add("active")
			}
		},
		error: function (msg) {
			if (t == "answer") {
				alert("你還沒回過任何問題")
			}
			else {
				error = msg;
			}
		}
	})
}

function addfilter(t, v) {
	if (v == null) {
		delete filter[t]
		document.getElementById("type-filter").innerHTML = "問題種類"
		getallquestion(select_type, select_values);
		return;
	}
	if (t == "type") {
		document.getElementById("type-filter").innerHTML = "問題種類 - " + q_typelist[v]
	}
	filter[t] = v
	getallquestion(select_type, select_values);
}

getallquestion(select_type, select_values);
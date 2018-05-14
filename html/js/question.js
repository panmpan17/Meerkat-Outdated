var question_id = null;
var filter = {}
var UPLOAD_LIMIT = 10 * 1024 * 1024;
page_f = "<li class=\"paging{1}\" onclick=\"changepage({0})\"><a>{0}</a></li>"
more_f = "<li class=\"paging\"\"><a>...</a></li>"

colormatch = [
	"#ffa31a",
	"#0066cc",
	"#fe3693",
	]

// 
// ASK QUESTION
//
function openask() {
	if (getCookie("id")) {
		show_popup("ask-frame");
	}
	else {
		if (confirm("請登錄")) {
			show_popup("login-frame");
		}
	}
}

// 
// CHANGE QUESTION TYPE
// 
var q_type = 0;
var select_type = "all";
var select_values = null;
var q_text = $("#dropdownMenu1")[0];
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
var IMAGE_TYPE = [
	".png",
	".gif",
	".jpeg",
	".jpg",
]
file_format = `<a target="_blank" class="file-link" download href="{0}">- 檔案 {1} - {2} </a><br`
image_fromat = `<img src="{0}" onclick="displayimg(this)" style="width: 300px;cursor: zoom-in;" />`

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

function pagging (selection, place) {
	if (selection.length <= 5) {
		return selection;
	}
	pages = new Set([selection[0], selection[selection.length - 1]]);
	
	pages.add(selection[place]);
	if (place > 1) {
		pages.add(selection[place - 1]);
	}
	if (place < selection.length - 1) {
		pages.add(selection[place + 1]);
	}

	pages = Array.from(pages).sort()

	last_page = pages[0] - 1
	add_more_icon = []
	$.each(pages, function (i, page) {
		if (page - last_page != 1) {
			add_more_icon.push(i + add_more_icon.length)
		}
		last_page = page
	})

	$.each(add_more_icon, function (_, icon) {
		pages.splice(icon, 0, "...");
	})
	return pages
}

card_format = `
<div class="card" onclick="openquestion({4})">
	<div class="card-solved" style="background-color:{3}"></div><div class="card-title">{0}</div>
	<br>
	<div class="card-author">{7}</div>
	<span class="card-time">{1}</span>
	&nbsp;&nbsp;&nbsp;
	<span class="card-type" style="background-color:{5}">{2}</span>
	&nbsp;&nbsp;&nbsp;
	<span class="card-reply">最後回應: {6}</span>
</div>
`

function to_questions (l) {
	// paging html
	len_pages = l["pages"]

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

	pages = Array.apply(null, Array(len_pages)).map(function (_, i) {return i + 1;});
	pages = pagging(pages, page - 1)
	for (i=0;i<pages.length;i++) {
		if (pages[i] == page) {
			paging += format(page_f, pages[i], " press");
			continue
		}
		if (pages[i] == "...") {
			paging += more_f
			continue
		}
		paging += format(page_f, pages[i], "");
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
	
	cards = "";
	if (l["pages"] > 0) {

		questions = l["questions"]
		$.each(questions, function (_, i) {
			solved_color = "Crimson" // unsolved
			if (i["solved"]) {
				solved_color = "LimeGreen";
			}

			reply = "尚無回答"
			if (i["answer_writer"] != undefined) {
				reply = i["answer_writer"] + "&nbsp;&nbsp;&nbsp;" + i["answer_create_at"]
			}

			card = format(card_format, i["title"],
				i["create_at"], 
				q_typelist[i["type"]],
				solved_color,
				i["id"],
				colormatch[i["type"]],
				reply,
				i["writer"])

			cards += card;
		})
	}

	else {
		cards = `
		<br />
		<br />
		<center>
			<div class="well well-lg" style="width:90%">
				沒有這類的問題
			</div>
		`
	}

	$("#page-control")[0].innerHTML = paging;
	$("#cards")[0].innerHTML = cards;
}

function displayimg (e) {
	show_popup("image-frame");
	$("#image-frame-image")[0].src = e.src;
}

function displayfile (filename, fileseq) {
	breaked = false
	$.each(IMAGE_TYPE, function (_, type) {
		if (filename.endsWith(type)) {
			breaked = true
			return false;
		}
	})
	if (breaked) {
		return format(image_fromat, filename)
	}
	return format(file_format, filename, fileseq, changefilename(filename))
}
// 
// SHOW SIGNLE QUESTION
// 
answer_format = `<hr />
<span id="writer"> {1} </span> <sup id="time"> {2} </sup><br />
<div style="padding-left:30px">
	{0}
</div>
`
function getanswer(qid) {
	string_param = {"qid": qid}
	$.ajax({
		url: host + "answer/",
		type: "GET",
		data: string_param,
		success: function (msg) {

			answers = ""
			for (i=0;i<msg["answers"].length;i++) {
				m = msg["answers"][i]

				var msg_content = m["content"].replace(/\n/g, "<br>");
				msg_content = msg_content.replace(/\t/g, "    ")
				msg_content = msg_content.replace(/    /g, `<span class="ident"></span>`)
				console.log(msg_content)
				answers += format(answer_format,
					msg_content,
					m["writer"],
					m["create_at"]
					)

				file_display = "<div style=\"padding-left:30px\">"
				if (m["file1"] != "") {
					file_display += displayfile(m["file1"], "1")

					if (m["file2"] != "") {
						file_display += displayfile(m["file2"], "2")
					}
					if (m["file3"] != "") {
						file_display += displayfile(m["file3"], "3")
					}
					answers += file_display + "</div></div>";
				}

			}
			answers += "<hr>"
			$("#answers")[0].innerHTML = answers;
		},
		error: function (msg) {
			$("#answers")[0].innerHTML = "<hr /> 目前沒有解答 <hr />";
			// NO ANSWER
		}
	})
}

function showquestion(qid) {
	string_param = {"id":qid}

	window.history.pushState({}, "", "question?q=" + qid)
	$.ajax({
		url: host + "question/",
		type: "GET",
		data: string_param,
		success: function (msg) {
			$("#answer-content")[0].value = "";

			var msg_content = msg["content"].replace(/\n/g, "<br>");
			msg_content = msg_content.replace(/    /g, `<span class="ident"></span>`)
			console.log(msg_content)
			$("#content")[0].innerHTML = msg_content;
			$("#type")[0].innerHTML = q_typelist[msg["type"]];
			$("#type")[0].style.backgroundColor = colormatch[msg["type"]]

			a = "<div id=\"solved\" style=\"background-color:"
			if (msg["solved"]) {
				a += "LimeGreen";
			}
			else {
				a += "Crimson";
			}
			a += "\"></div> " + msg["title"];
			$("#title")[0].innerHTML = a;
			$("#create_at")[0].innerHTML = msg["create_at"];
			$("#question-writer")[0].innerHTML = msg["writer"];
			
			if (getCookie("id") != msg["writer_id"]) {
				$("#closequestion")[0].disabled = true;
				$("#closequestion")[0].onclick = null;
			}
			else {
				document.getElementById("closequestion").disabled = false;
				if (msg["solved"]) {
					$("#closequestion")[0].onclick = function () {closequestion("False")};
					$("#closequestion")[0].innerHTML = "開啟問題";
				}
				else {
					$("#closequestion")[0].onclick = function () {closequestion("True")};
					$("#closequestion")[0].innerHTML = "關閉問題";
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
				file_display += displayfile(msg["file1"], "1")
				if (msg["file2"] != "") {
					file_display += displayfile(msg["file2"], "2")
				}
				if (msg["file3"] != "") {
					file_display += displayfile(msg["file3"], "3")
				}
				$("#files")[0].innerHTML = file_display;
			}
			else {
				$("#files")[0].innerHTML = "沒有檔案";
			}

			getanswer(qid);
			question_id = qid;
		},
		error: function (msg) {
			hide_popup("question-frame")
		}
	})
}

function openquestion (id) {
	show_popup("question-frame");
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
				show_popup("login-frame");
			}
		}
	})
}

function answer() {
	content = $("#answer-content")[0].value;

	if (content) {
		json = {
			"key": getCookie("key"),
			"content": content,
			"writer": getCookie("id"),
			"answer_to": question_id,
		}
		$.ajax({
			url: host + "answer/",
			type: "POST",
			dataType: "json",
			data: JSON.stringify(json),
			contentType: "application/json; charset=utf-8",
			success: function (msg) {
				f1 = checkfile("f1-a");
				f2 = checkfile("f2-a");
				f3 = checkfile("f3-a");
				if (f1 || f2 || f3) {
					$("#answerkey")[0].value = msg["answer_id"]
					$("#answerform")[0].submit()
				}
				else {
					$("[name=ask-content]").value = "";
					showquestion(question_id)
				}
			},
			error: function (msg) {
				reload = confirm("請重新登錄");
				if (reload) {
					hide_popup('question-frame');
					show_popup("login-frame");
				}
			}
		})
	}
	else {
		alert("請不要留空")
	}
}

function ask() {
	errormsg = $("#ask-errormsg")[0];

	title = $("#ask-title")[0].value
	content = $("#ask-content")[0].value;
	if (title && content) {
		key = getCookie("key");
		json = {
			"key": key,
			"title": title,
			"content": content,
			"type": q_type,
		}
		$.ajax({
			url: host + "question/",
			type: "POST",
			dataType: "json",
			data: JSON.stringify(json),
			contentType: "application/json; charset=utf-8",
			success: function (msg) {
				f1 = checkfile("f1-q");
				f2 = checkfile("f2-q");
				f3 = checkfile("f3-q");
				if (f1 || f2 || f3) {
					$("#questionkey")[0].value = msg["question_id"];
					$("#questionform")[0].submit();
				}
				else {
					$("#ask-title")[0].value = "";
					$("#ask-content")[0].value = "";
					hide_popup("ask-frame");
					openquestion(msg["question_id"]);
					getallquestion(select_type, select_values);
				}
			},
			error: function (error) {
				p1 = error.responseText.indexOf("<p>") + 3
				errortype = error.responseText.substring(p1, error.responseText.indexOf("</p>", p1))

				if (errortype == "User is not active") {
					alert("請先進行email認證後才能發表問題")
					return;
				}

				reload = confirm("請重新登錄");
				if (reload) {
					hide('ask-frame');
					show_popup("login-frame");
				}
			}
		})
	}
	else {
		alert("請不要留空")
	}
}

function getallquestion(t, v) {
	if (t == "all") {
		$("#question-range-btn")[0].innerHTML = " 問題範圍 : 所有問題 "
	}

	if (((t == "writer") || (t == "answer")) && (v == "")) {
		reload = confirm("請登錄");
		if (reload) {
			show_popup("login-frame");
		}
		return null;
	}
	else if (t == "writer") {
		$("#question-range-btn")[0].innerHTML = " 問題範圍 : 我的問題 "
	}
	else if (t == "answer") {
		$("#question-range-btn")[0].innerHTML = " 問題範圍 : 回答過的問題 "
	}

	select_values = v
	if (select_values == "True") {
		$("#question-range-btn")[0].innerHTML = " 問題範圍 : 已解問題 ";
	}
	if (select_values == "False") {
		$("#question-range-btn")[0].innerHTML = " 問題範圍 : 未解的問題 ";
	}

	if (select_type != t) {
		page = 1;
		select_type = t;
	}

	$("#cards")[0].innerHTML = '<span style="font-size:48px;color:#aaa">請稍等</span>';
	string_param = {"page": page - 1}
	string_param[t] = select_values
	$.ajax({
		url: host + "question/",
		type: "GET",
		data: jQuery.extend(string_param, filter),
		success: function (msg) {
			to_questions(msg);
			page_limit = msg["pages"]

			// if (t == "answer") {
			// 	$(".active")[0].classList.remove("active");
			// 	$("#" + t)[0].classList.add("active")
			// }
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
		$("#question-type-btn")[0].innerHTML = "問題種類 - 全部"
		getallquestion(select_type, select_values);
		return;
	}
	if (t == "type") {
		$("#question-type-btn")[0].innerHTML = "問題種類 - " + q_typelist[v]
	}
	filter[t] = v
	getallquestion(select_type, select_values);
}

function hidequestion() {
	hide_popup('question-frame');
	window.history.pushState({}, "", "question")
}

multi_file_btn_data = {}
input_2_label = {}
files_format = `<tr><td class="filename">{0}</td><td class="delete-file" onclick="delete_file('{1}', '{2}')"></td></tr>`

function format() {
    var s = arguments[0];
    for (var i = 0; i < arguments.length - 1; i++) {       
        var reg = new RegExp("\\{" + i + "\\}", "gm");             
        s = s.replace(reg, arguments[i + 1]);
    }
    return s;
}

function find_input (lid) {
	var new_for = false;
	var files_html = ""

	$.each(multi_file_btn_data[lid], function (_, i_id) {
		input_ele = $("#" + i_id)[0]

		if (input_ele.value == "") {
			if (!new_for) {
				$("#" + lid)[0].setAttribute("for", input_ele.id);
				new_for = true;
			}
		}
		else {
			files_html += format(
				files_format,
				input_ele.value,
				lid,
				input_ele.id,
				)
		}
	})
	$("#" + lid + "-files")[0].innerHTML = files_html
	// console.log(files_html)
	if (!new_for) {
		$("#" + lid)[0].setAttribute("for", "file-full");
	}
}

function delete_file (label_id, input_id) {
	$("#" + input_id)[0].value = "";
	find_input(label_id);
}

function file_full () {
	alert("檔案上傳數量已達上限 !")
}

// title_re = /[a-zA-Z0-9!,.，。！\-\+=_]{1,50}/g;
// function checktitle (e) {
// 	if (matchRE(title_re, e.value)) {
// 		e.parentNode.classList.remove("has-error")
// 		e.parentNode.classList.add("has-success")
// 	}
// 	else {
// 		e.parentNode.classList.add("has-error")
// 		e.parentNode.classList.remove("has-success")
// 	}
// }

$(document).ready(function () {
	$.each($(".multi-file-btn"), function (_, btn) {
		var for_list = btn.attributes["for-list"].value.split(" ");
		var element_list = [];
		$.each(for_list, function (_, id) {
			$("#" + id)[0].onchange = function (e) {
				e = e.target
				accept = e.accept.split(",")
				filename = e.files[0]["name"]

				breaked = false;
				$.each(accept, function (_, i) {
				    if (filename.endsWith(i)) {
				        breaked = true;
				        return false;
				    } 
				})
				if (!breaked) {
				    alert("檔案格式不合");
				    e.value = ""
				    return;
				}
				else if (e.files[0].size > UPLOAD_LIMIT) {
					alert("檔案過大");
					e.value = ""
					return
				}
				else {
					find_input(input_2_label[e.id])
				}
			}
			element_list.push(id)
			input_2_label[id] = btn.id
		})
		
		multi_file_btn_data[btn.id] = element_list;
	})
	$.each(multi_file_btn_data, function (i) {
		find_input(i)
	})


	getallquestion(select_type, select_values);

	try {
		params = location.search.replace("?", "")
		qstart = params.indexOf("q=")
		qend = params.indexOf("&", qstart)
		if (qend == -1) {
			qend = params.length
		}
		num = params.substring(qstart + 2, qend)
		if (num != "") {
			num = parseInt(num)
			openquestion(num)
		}
	}
	catch (error) {}
})

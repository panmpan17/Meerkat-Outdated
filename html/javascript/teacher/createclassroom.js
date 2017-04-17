student_field_scratch_format = `\
<tr>
	<td>{0}</td>
	<td class="bg-success" id="cid-{1}">{1}</td>
	<td id="sid-{2}"">{2}</td>
</tr>
`

student_field_python_format = `\
<tr>
	<td>{0}</td>
	<td class="bg-success" id="cid-{1}">{1}</td>
</tr>
`

sid_colors = {};
function remove_blank() {
	f = $("#field")[0]
	f.value = f.value.replace(/\t/g, ",")
	f.value = f.value.replace(/     /g, ",")
	f.value = f.value.replace(/    /g, ",")
	f.value = f.value.replace(/   /g, ",")
	f.value = f.value.replace(/  /g, ",")
	f.value = f.value.replace(/ /g, ",")
}

function check_students() {
	classroom_name = $("#classroom-name")[0].value;
	if (classroom_name == "") {
		alert("教室名稱不能留白");
		return;
	}
	f = $("#field")[0]
	if (f.value == "") {
		alert("學生資料欄位不能留空");
		return
	}

	type = $("#select-type")[0].value
	if (type == "scratch_1" || type == "teacher_1") {
		check_students_scratch()
	}
	else if (type == 'python_01') {
		check_students_python()
	}
	else {
		// pass
	}
}

function check_students_scratch() {
	classroom_name = $("#classroom-name")[0].value;
	data = f.value.split("\n")

	students_table = $("#students")[0];
	students_table .innerHTML = "";

	names = [];
	cids = [];
	sids = [];
	for (i=0;i<data.length;i++) {
		student = data[i].split(",")
		if (student.length < 3) {
			alert("學生資料不完整請檢查");
			return;
		}

		name = student[0];cid = student[1];sid = student[2];

		names.push(name)
		cids.push(cid)
		sids.push(sid)

		sid = sid.toLowerCase();
		sid_colors[sid] = false;
		$.ajax("https://scratch.mit.edu/users/" + sid).done(function (msg) {
			sname = msg.substring(msg.indexOf("<title>") + 7, msg.indexOf(" on Scratch</title>"));
			sname = sname.toLowerCase();
			sid_colors[sname] = true;
		})
		$("#students")[0].innerHTML += format(student_field_scratch_format,
			name,
			cid,
			sid)
	}
	$.ajax({
		url: host + "teacher/user",
		data: {"tkey": getCookie("teacher-key"), "users": cids},
		success: function (msg) {
			for (i=0;i<msg["none"].length;i++) {
				document.getElementById("cid-" + msg["none"][i]).classList.remove("bg-success")
				document.getElementById("cid-" + msg["none"][i]).classList.add("bg-danger")
			}
		}
	})

	$("#studentsthead")[0].innerHTML = "<tr><th>學生姓名</th><th>Coding 4 Fun 帳號</th><th>Scratch 帳號</th></tr>"
	$("#s-students-table").show()
	$("#bg").show()

	setTimeout(function () {
		$.each(sid_colors, function (k,v) {
			k = k.toLowerCase()
			if (v) {
				document.getElementById("sid-" + k).classList.add("bg-success")
			}
			else {
				document.getElementById("sid-" + k).classList.add("bg-danger")
			}
		})
		$("#bg").hide();

		if ($(".bg-danger").length == 0) {
			c = confirm("創建教室");
			if (c) {
				json = {
					"tkey": getCookie("teacher-key"),
					"students_name": names,
					"students_cid": cids,
					"students_sid": sids,
					"type": $("#select-type")[0].value,
					"name": classroom_name,
				}

				$.ajax({
					url: host + "classroom/",
					type: "POST",
					dataType: "json",
					data: JSON.stringify(json),
					contentType: "application/json; charset=utf-8",
					success: function (msg) {
						location.reload();
					}
				})
			}
		}
	}, (2000 * Object.keys(sid_colors).length));
}

function check_students_python() {
	classroom_name = $("#classroom-name")[0].value;
	data = f.value.split("\n")

	students_table = $("#students")[0];
	students_table.innerHTML = "";

	names = [];
	cids = [];
	for (i=0;i<data.length;i++) {
		student = data[i].split(",")
		if (student.length < 2) {
			alert("學生資料不完整請檢查");
			return;
		}

		name = student[0];cid = student[1];

		names.push(name)
		cids.push(cid)

		$("#students")[0].innerHTML += format(student_field_python_format,
			name,
			cid)
	}
	$.ajax({
		url: host + "teacher/user",
		data: {"tkey": getCookie("teacher-key"), "users": cids},
		success: function (msg) {
			for (i=0;i<msg["none"].length;i++) {
				document.getElementById("cid-" + msg["none"][i]).classList.remove("bg-success")
				document.getElementById("cid-" + msg["none"][i]).classList.add("bg-danger")
			}
		}
	})

	$("#studentsthead")[0].innerHTML = "<tr><th>學生姓名</th><th>Coding 4 Fun 帳號</th></tr>"
	$("#s-students-table").show()

	if ($(".bg-danger").length == 0) {
		c = confirm("創建教室");
		if (c) {
			json = {
				"tkey": getCookie("teacher-key"),
				"students_name": names,
				"students_cid": cids,
				"students_sid": [],
				"type": $("#select-type")[0].value,
				"name": classroom_name,
			}

			$.ajax({
				url: host + "classroom/",
				type: "POST",
				dataType: "json",
				data: JSON.stringify(json),
				contentType: "application/json; charset=utf-8",
				success: function (msg) {
					location.reload();
				}
			})
		}
	}
}


function changeclassroomtype() {
	type = $("#select-type")[0].value

	if ((type == 'python_01') || (type == "scratch_1") || (type == "teacher_1")) {
		$("#students_info").show()
		$("#hoverimg").show()
		$("#check_students_b")[0].innerHTML = `<i class="fa fa-check" aria-hidden="true"></i> 檢查學生資料`

		if ((type == "scratch_1") || (type == "teacher_1")) {
			$("#hoverimg")[0].src = "html/images/scratch_table.png"
		}
		else {
			$("#hoverimg")[0].src = "html/images/python_table.png"
		}
	}
	else {
		$("#students_info").hide()
		$("#hoverimg").hide()
		$("#check_students_b")[0].innerHTML = `<i class="fa fa-check" aria-hidden="true"></i> 建立教室`
	}
}
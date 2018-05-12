// this one check user's userid password
id_pass_re = new RegExp("[a-zA-Z0-9@\.]{8,32}");
// file_re = new RegExp("[0-9]+_[0-9]+")
email_re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
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

function login () {
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

				window.location.reload();
			},
			error: function (error) {
				errormsg = $("#login-errormsg")[0]
				p1 = error.responseText.indexOf("<p>") + 3
				errortype = error.responseText.substring(p1, error.responseText.indexOf("</p>", p1))
				if (errortype == "Username or password wrong") {
					errormsg.innerHTML = "帳號或密碼不正確";
				}
				else if (errortype.indexOf("disable") > -1) {
					errormsg.innerHTML = "帳號已被封鎖"
				}
				return
			}
		})
	}
	else {
		errormsg.innerHTML = "帳號或密碼欄位請不要留空白"
		show("login-errormsg");
		return 
	}
}

function signup () {
	errormsg = $("#signup-errormsg")[0]

	userid = $("[name=signup-userid]")[0].value;
	password = $("[name=signup-password]")[0].value;
	repassword = $("[name=signup-repassword]")[0].value;
	email = $("[name=signup-email]")[0].value;
	birth = $("[name=signup-birth_year]")[0].value;
	nickname = $("[name=signup-nickname]")[0].value;
	job = $("[name=signup-job]")[0].value;
	
	human = grecaptcha.getResponse()
	//active = "True";
	//type = "1";
	
	// check every things is not empty and valid
	if (userid && password && repassword && email && birth && nickname) {
		//id_valid = matchRE(id_pass_re, userid);
		pass_valid = matchRE(id_pass_re, password);
		email_valid = matchRE(email_re, email);
		/*
		if (!id_valid) {
			errormsg.innerHTML = "帳號並不符合格式";
			return
		}*/
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
		errormsg.innerHTML = "必填項目請不要留空白";
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
		//"active":active,
		//"type":type,
	}

	if (job) {
		json["job"] = job;
	}

	$.ajax({
		url: host + "user/",
		type: "POST",
		dataType: "json",
		data: JSON.stringify({"recapcha": human, users: [json]}),
		//data: JSON.stringify({users: [json]}),
		contentType: "application/json; charset=utf-8",
		success: function (msg) {
			storeCookie("id", msg["lastrowid"]);
			storeCookie("userid", msg["userid"]);
			storeCookie("key", msg["key"]);
			
			window.location.reload();
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

function logout () {
	deleteCookie("id");
	deleteCookie("userid");
	deleteCookie("key");

	window.location.reload();
}

/*
function red () {
	key = getCookie("key");
	id = getCookie("id");
	string_param = {"key":key, "id":id}	
	
	$.ajax({
		url: host + "user/red",
		type: "GET",		
		data: string_param,
		success: function (msg) {
			//alert("test function ok");
		},
		error: function (msg) {
			reload = confirm("請重新登錄");
			if (reload) {
				$("#info-frame").modal("hide");
				show_popup("login-frame");
			}
		}
	})
	
}
*/

function showinfo () {
	key = getCookie("key");
	id = getCookie("id");
	string_param = {"key":key, "id":id}
	$.ajax({
		url: host + "user/",
		type: "GET",
		data: string_param,
		success: function (msg) {
			$("#change-nickname")[0].value = msg["nickname"]
			$("#info-userid")[0].innerHTML = msg["userid"];
			// $("#info-point")[0].innerHTML = msg["point"];
			$("#info-nick")[0].innerHTML = msg["nickname"];
			$("#info-birth")[0].innerHTML = msg["birth_year"];
			$("#info-job")[0].innerHTML = msg["job"];

			if (msg["active"]) {
				$("#info-email")[0].innerHTML = msg["email"];
			}
			else {
				$("#info-email")[0].innerHTML = msg["email"];
			}

			// $("#info-level")[0].innerHTML = "一般";
			// point = msg["point"];
			// if (point > 200) {$("#info-level")[0].innerHTML = "鑽石"}
			// else if (point > 100) {$("#info-level")[0].innerHTML = "白金"}
			// else if (point > 20) {$("#info-level")[0].innerHTML = "黃金"}

			if (msg["active"]) {
				$("#info-active #success").show();
				$("#info-active #resent").hide();
				$("#info-active #checkcode").hide();
			}
			else {
				$("#info-active #success").hide();

				if (msg["email_valid"]) {
					$("#info-active #checkcode").show();
					$("#info-active #resent").hide();
				}
				else {
					$("#info-active #checkcode").hide();
					$("#info-active #resent").show();
				}
			}

			if (!msg["admin"]) {
				try {
					$("#userinfo")[0].childNodes[1].removeChild($("#info-admin")[0])
				}
				catch(err) {}
			}
			if (msg["type"] == 0) {
				try {
					$("#userinfo")[0].childNodes[1].removeChild($("#info-teacher")[0])
				}
				catch(err) {}
			}
			
			// for test
			/*
			if (msg["nickname"] != 'Greentea')
			{
				try {
					$("#userinfo")[0].childNodes[1].removeChild($("#info-test")[0])
				}
				catch(err) {}
			}
			*/
			
			$("#info-frame").modal("show");
		},
		error: function (msg) {
			reload = confirm("請重新登錄");
			if (reload) {
				show_popup("login-frame");
			}
		}
	})
}

function resentmail () {
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
				$("#info-frame").modal("hide");
				show_popup("login-frame");
			}
		}

	})
}

function changepassword () {
	password = $("#change_password")[0].value;
	newpassword = $("#change_newpassword")[0].value;
	check_password = $("#change_check_password")[0].value;

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
			$("#info-frame").modal("hide");
			show_popup("login-frame");
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

function checkenumber () {
	code = $("#code")[0].value;
	if (code == "") {
		alert("不可留白");
	}
	else {
		location.pathname = "/active/" + code
	}
}

function hide_allpopup () {
	$("#black-bg").hide();
	$(".popup-frame").hide()
}

function hide_popup (pop_id) {
	$("#black-bg").hide();
	$("#" + pop_id).hide();
}

function show_popup (pop_id) {
	$("#black-bg").show();
	$("#" + pop_id).show();
}

function checknewpassword (e) {
	pass_valid = matchRE(id_pass_re, e.value);
	if (pass_valid) {
		$("#newpasvalind")[0].innerHTML = "✔";
		$("#newpasvalind")[0].style.color = "rgb(62, 117, 63)";
		$("#newpasvalind")[0].style.backgroundColor = "rgb(223, 240, 217)";

	}
	else {
		$("#newpasvalind")[0].innerHTML = "✖";
		$("#newpasvalind")[0].style.color = "rgb(167, 69, 68)";
		$("#newpasvalind")[0].style.backgroundColor = "rgb(242, 222, 222)";
	}
}

function checknewrepassword (e) {
	if (e.value == $("#change_newpassword")[0].value) {
		$("#newrepasvalind")[0].innerHTML = "✔";
		$("#newrepasvalind")[0].style.color = "rgb(62, 117, 63)";
		$("#newrepasvalind")[0].style.backgroundColor = "rgb(223, 240, 217)";

	}
	else {
		$("#newrepasvalind")[0].innerHTML = "✖";
		$("#newrepasvalind")[0].style.color = "rgb(167, 69, 68)";
		$("#newrepasvalind")[0].style.backgroundColor = "rgb(242, 222, 222)";
	}
}

function show_change_page () {
	if ($("#userinfochange")[0].hidden) {
		$("#userinfochange")[0].hidden = false;
		$("#userinfochange-txt")[0].innerHTML = "返回";
		$("#userinfo").hide();
	}
	else {
		$("#userinfochange")[0].hidden = true;
		$("#userinfochange-txt")[0].innerHTML = "修改資料";
		$("#userinfo").show();
	}
}

function change_baseinfo () {
	nickname = $("#change-nickname")[0].value
	job = $("#change-job")[0].value

	if (nickname == "") {
		alert("暱稱必須填寫")
		return;
	}

	json = {
		"key": getCookie("key"),
		"nickname": nickname,
		"job": job,
	}
	$.ajax({
		url: host + "user/",
		type: "PUT",
		dataType: "json",
		data: JSON.stringify(json),
		contentType: "application/json; charset=utf-8",
		success: function (msg) {
			alert("更改成功 (建議重新整理頁面)");
		},
		error: function (err) {
			console.log(err)
		}
	})
}

function fgpwdcheckuserid () {
	userid = $("#fgpwd-userid")[0].value;

	$.ajax({
		url: host + "user/password",
		data:{
			"userid": userid
		},
		success: function (msg) {
			if (msg["success"]) {
				$("#fgpwd-step1").hide();
				$("#fgpwd-step2").show(300);
				id = $("#fgpwd-id")[0].value = msg["id"];
			}
			else {
				$("#fgpwd-step1-errormsg")[0].innerHTML = "這帳號不存在";
			}
		}
	})
}

function fgpwdsendmail () {
	id = $("#fgpwd-id")[0].value;
	userid = $("#fgpwd-userid")[0].value;
	nickname = $("#fgpwd-nickname")[0].value;
	email = $("#fgpwd-email")[0].value;

	$.ajax({
		url: host + "user/password",
		type: "POST",
		dataType: "json",
		data: JSON.stringify({
			"id": id,
			"userid": userid,
			"nickname": nickname,
			"email": email,
		}),
		contentType: "application/json; charset=utf-8",
		success: function (msg) {
			if (msg["success"]) {
				$("#fgpwd-id")[0].value = "";
				$("#fgpwd-userid")[0].value = "";
				$("#fgpwd-nickname")[0].value = "";
				$("#fgpwd-email")[0].value = "";

				$("#fgpwd-step1").show();
				$("#fgpwd-step2").hide();

				hide_popup("forget-pwd-frame");
				console.log(msg)
				alert("更改成功去檢查 Email");
			}
			else {
				$("#fgpwd-step1-errormsg")[0].innerHTML = "認證失敗";
			}
		}
	})
}
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

host = "http://" + window.location.host + "/rest/1/"

// this one check user's userid password
id_pass_re = /\w{8,16}/;
email_re = /\w+@\w+(.\w+)*/;

function login() {
	errormsg = document.getElementById("login-errormsg")

	userid = document.getElementsByName("login-userid")[0].value;
	password = document.getElementsByName("login-password")[0].value;
	password = sha256(password);
	if (userid && password) {
		json = {"userid":userid, "password":password}
		$.ajax({
			url: host + "logon/",
			type: "POST",
			dataType: "json",
			data: JSON.stringify(json),
		    contentType: "application/json; charset=utf-8",
			success: function (msg) {
				storeCookie("id", msg["lastrowid"]);
				storeCookie("userid", msg["userid"]);
				storeCookie("key", msg["key"]);
				location.reload();
			},
			error: function (error) {
				errormsg = document.getElementById("login-errormsg")
				p1 = error.responseText.indexOf("<p>") + 3
				errortype = error.responseText.substring(p1, error.responseText.indexOf("</p>", p1))
				if (errortype == "Username or password wrong") {
					errormsg.innerHTML = "帳號密碼不正確";
				}
				return 
			},
		})
	}
	else {
		errormsg.innerHTML = "請不要留空白"
		show("login-errormsg");
		return 
	}
}

function signup(){
	errormsg = document.getElementById("signup-errormsg")

	userid = document.getElementsByName("signup-userid")[0].value;
	password = document.getElementsByName("signup-password")[0].value;
	repassword = document.getElementsByName("signup-repassword")[0].value;
	email = document.getElementsByName("signup-email")[0].value;
	birth = document.getElementsByName("signup-birth_year")[0].value;
	nickname = document.getElementsByName("signup-nickname")[0].value;
	job = document.getElementsByName("signup-job")[0].value;

	human = grecaptcha.getResponse()

	// check every things is not empty and valid
	if (userid && password && repassword && email && birth && nickname) {
		id_valid = id_pass_re.test(userid);
		pass_valid = id_pass_re.test(password);
		email_valid = email_re.test(email);
		if (id_valid == false) {
			errormsg.innerHTML = "帳號並不符合格式";
			return
		}
		if (pass_valid == false) {
			errormsg.innerHTML = "密碼並不符合格式";
			return
		}
		if (email_valid == false) {
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
			userid = document.getElementsByName("signup-userid")[0].value;
			storeCookie("id", msg["lastrowid"]);
			storeCookie("userid", msg["userid"]);
			storeCookie("key", msg["key"]);
			location.reload();
		},
		error: function (error) {
			errormsg = document.getElementById("signup-errormsg")
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
	document.getElementById("info-userid").innerHTML = dict["userid"];
	document.getElementById("info-point").innerHTML = dict["point"];
	document.getElementById("info-nick").innerHTML = dict["nickname"];
	document.getElementById("info-email").innerHTML = dict["email"];
	document.getElementById("info-birth").innerHTML = dict["birth_year"];
	document.getElementById("info-job").innerHTML = dict["job"];

	document.getElementById("info-level").innerHTML = "一般";
	point = dict["point"];
	if (point > 200) {document.getElementById("info-level").innerHTML = "鑽石"}
	else if (point > 100) {document.getElementById("info-level").innerHTML = "白金"}
	else if (point > 20) {document.getElementById("info-level").innerHTML = "黃金"}

	if (dict["admin"]) {
		tr = document.createElement("tr")

		td1 = document.createElement("td")
		td1.appendChild(document.createTextNode("Admin"))

		td2 = document.createElement("td")
		a = document.createElement("a")
		a.appendChild(document.createTextNode("True"))
		a.href = "/admin"
		a.style.color = "#000"
		td2.appendChild(a)

		tr.appendChild(td1)
		tr.appendChild(td2)

		document.getElementById("userinfo").appendChild(tr)
	}
}

function showinfo() {
	show('info-frame');
	hide('accountmenu');

	key = getCookie("key");
	id = getCookie("id");
	string_param = {"key":key, "id":id}
	back = $.ajax({
		url: host + "user/",
		type: "GET",
		data: string_param,
		success: function (msg) {
			s = to_html(msg);
			// console.log(s);
		},
		error: function (msg) {
			reload = confirm("請重新登錄");
			if (reload) {
				hide('info-frame');
				show("login-frame");
			}
		}
	})
	return back;
}
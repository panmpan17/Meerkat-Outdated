$('.newPost button[data-func]').click(function(){
	document.execCommand( $(this).data('func'), false 	);
});
$('.newPost select[data-func]').click(function(){
	var $value = $(this).find(':selected').val();
	if ($value == "selfColor") {
		color = prompt("自訂顏色:\n(ex: Red, Black, #F00, #000)")
		document.execCommand( "foreColor", false, color);
		return null;
	}
	document.execCommand( $(this).data('func'), false, $value);
})

$('#size').on('change', function() {
	var size = $(this).val();
	$('.editor').css('fontSize', size + 'px');
});
link_edit_fmt = "[#連結外表#]\{\#連結網址\#\}";
function addlink() {
	$(".editor").html($(".editor").html() + link_edit_fmt)
}

function preview(){
	html = turn_url($(".editor").html());
	$("#review").html(html);
}

function post() {
	tf = confirm("是否要發布")
	if (!tf) {
		return 
	}
	content = turn_url($(".editor").html());
	if (content == "") {
		alert("請不要留空");
		return;
	}

	json = {"key": getCookie("key"),
		"content": content}
	$.ajax({
		url: window.location.origin + "/rest/1/post/",
		type: "POST",
		dataType: "json",
		data: JSON.stringify(json),
		contentType: "application/json; charset=utf-8",
		success: function (msg) {
			window.location.pathname = "news"
		},
		error: function (msg) {
			error = msg;
		}
	})
}

function format() {
	var s = arguments[0];
	for (var i = 0; i < arguments.length - 1; i++) {       
		var reg = new RegExp("\\{" + i + "\\}", "gm");             
		s = s.replace(reg, arguments[i + 1]);
	}
	return s;
}

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

news_format = `
<tr>
	<td style="border-bottom: 1px solid #ddd;">{1}</td>
	<td style="border-bottom: 1px solid #ddd;padding:10px;">{0}</td>
	<td style="border-bottom: 1px solid #ddd;">
		<a onclick="deletepost('{1}')" style="color:red;font-weight:bold;">X</a>
	</td>
</tr>
`

function loadnews() {
	$.ajax({
		url: window.location.origin + "/rest/1/post/",
		type: "GET",
		success: function (msg) {
			posts = msg["posts"];

			if (posts.length > 0) {
				news = "";
				for (i = 0; i < posts.length; i++) {
					news += format(news_format, posts[i]["content"], posts[i]["id"])
				}
				document.getElementById("posts").innerHTML = news;
			}
		}
	})
}
loadnews()

function deletepost(id) {
	c = prompt("你確定要刪除這個發佈?\n如果是的話請輸入發佈的 Id")
	if (c != id) {
		alert("輸入失敗")
		return ;
	}
	url = window.location.origin + "/rest/1/post/?id={0}&key={1}"
	$.ajax({
		url: format(url, id, getCookie("key")),
		type: 'DELETE',
		success: function(result) {
			window.location.reload()
		}
	});
}

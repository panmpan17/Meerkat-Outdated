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
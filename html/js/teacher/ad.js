adclass_format = `
<tr>
	<td>{0}</td>
	<td>{1}</td>
	<td>{2}</td>
	<td>{3}</td>
	<td>{4}</td>
	<td>{5}</td>
	<td>{6}</td>
	<td class="b-close" onclick="deleteadclass('{7}')"><i class="fa fa-times"></i></td>
</tr>
`

chinese_weekday = [
	"",
	"星期一",
	"星期二",
	"星期三",
	"星期四",
	"星期五",
	"星期六",
	"星期日",
]

function newadclass() {
	address = $("#class-address")[0].value;
	type = $("#class-type")[0].value;
	date = getdate("classdate");
	enddate = getdate("classenddate");
	start_time = gettime(1);
	end_time = gettime(2);

	weekdays = []
	weekdaysdom = $("[name=weekdays]")
	$.each(weekdaysdom, function (i) {
		if (weekdaysdom[i].checked) {
			weekdays.push(parseInt(weekdaysdom[i].value))
		}
	})

	if (address == "") {
		alert("地址不能留空");
		return
	}
	if (date == "") {
		alert("開始日期必須選");
		return
	}
	if (weekdays.lenth == 0) {
		alert("上課日至少要有一個");
		return
	}

	json = {
	    "key": getCookie("key"),
	    "address": address,
	    "type": type,
	    "date": date,
	    "enddate": enddate,
	    "start_time": start_time,
	    "end_time": end_time,
	    "weekdays": weekdays,
	    }

	$.ajax({
		url: host + "adclass/",
		type: "POST",
		dataType: "json",
		data: JSON.stringify(json),
		contentType: "application/json; charset=utf-8",
		success: function (msg) {
			loadadclass();
		},
		error: function (error) {
			console.log(error)
		}
	})
}

function deleteadclass(aid) {
	c = confirm("你確定要刪除這個招生文?")
	if (!c) {
		return;
	}
	json = {"key": getCookie("key"), "aid": aid}
	$.ajax({
		url: host + "adclass/?" + $.param(json),
		type: "DELETE",
		success: function(result) {
			loadadclass();
		}
	});
}

function loadadclass() {
	$.ajax({
		url: host + "adclass/",
		type: "GET",
		data: {"teacher": true,
			"key": getCookie("key")},
		success: function (msg) {
			$("#tadclass")[0].innerHTML = "";

			console.log(msg)
			$.each(msg["adclasses"], function (_, i) {
				c_weekdays = []
				$.each(i["weekdays"], function (_, weekday) {
					c_weekdays.push(chinese_weekday[weekday])
				})

				enddate = ""
				if (i["enddate"]) {
					enddate = i["enddate"]
				}

				$("#tadclass")[0].innerHTML += format(
					adclass_format,
					CLASS_TO[i["type"]],
					i["date"],
					enddate,
					c_weekdays,
					i["start_time"],
					i["end_time"],
					i["address"],
					i["id"]);
			})
		}
	})
}
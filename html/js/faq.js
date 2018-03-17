$(".question").on("click", function (e) {
	e.currentTarget.classList.toggle("detail")
})

$(".my-sidebar .item").on("click", function (e) {
	$(".my-sidebar .item.active")[0].classList.remove("active");
	e.currentTarget.classList.add("active");
	$(".question").hide();
	console.log($(".question[name=FAQ-" + e.currentTarget.id + "]"))
	$(".question[name=FAQ-" + e.currentTarget.id + "]").show();
})

$(document).ready(function () {
	$(".question[name=FAQ-1]").show();
})
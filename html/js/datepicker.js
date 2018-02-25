$(function() {
  $( ".calendar" ).datepicker({
		dateFormat: 'dd/mm/yy',
		firstDay: 1
	});
	
	$(document).on('click', '.date-picker .input', function(e){
		var $me = $(this),
				$parent = $me.parents('.date-picker');
		$parent.toggleClass('open');
	});
	
	
	$(".calendar").on("change",function(){
		var $me = $(this),
			$selected = $me.val(),
			$parent = $me.parents('.date-picker');

		selected = $selected
		selected = selected.split("/")
		selected.reverse()
		selected = selected.join("/")

		$parent.find('.result').children('span').html(selected);
	});


	// TIME PICK BY MY SELF
	$(".hourup").mousedown(function () {
	  hour = $("#hour" + $(this)[0].id)[0].textContent;
	  hour = parseInt(hour);
	  hour += 1
	  
	  if (hour <= 12) {
	    $("#hour" + $(this)[0].id)[0].innerHTML = hour;
	  }
	})

	$(".hourdown").mousedown(function () {
	  hour = $("#hour" + $(this)[0].id)[0].textContent;
	  hour = parseInt(hour);
	  hour -= 1
	  
	  if (hour >= 1) {
	    $("#hour" + $(this)[0].id)[0].innerHTML = hour;
	  }
	})

	$(".minup").mousedown(function () {
	  min = $("#min" + $(this)[0].id)[0].textContent;
	  min = parseInt(min);
	  min += 15
	  
	  if (min <= 59) {
	    $("#min" + $(this)[0].id)[0].innerHTML = min;
	  }
	})

	$(".mindown").mousedown(function () {
	  min = $("#min" + $(this)[0].id)[0].textContent;
	  min = parseInt(min);
	  min -= 15
	  
	  if (min >= 0) {
	    $("#min" + $(this)[0].id)[0].innerHTML = min;
	  }
	})

	$(".ampmb").mousedown(function() {
	  ampm = $(this)[0].textContent;
	  
	  if (ampm == "AM") {
	    $(this)[0].innerHTML = "PM"
	  }
	  else {
	    $(this)[0].innerHTML = "AM"
	  }
	})

	
});

function gettime(eid) {
  hour = $("#hour" + eid)[0].textContent;
  min = $("#min" + eid)[0].textContent;
  ampm = $("#ampmb" + eid)[0].textContent;
  return hour + ":" + min + " " + ampm;
}

function getdate(eid) {
	selected = $("#" + eid)[0].textContent;
	selected = selected.split("/")
	selected.reverse()
	selected = selected.join("/")
	return selected
}

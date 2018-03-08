// JavaScript Document
$(function(){
	// 幫 a.scrolltop 加上 click 事件
	$('a.scrolltop').click(function(){
		// 讓捲軸用動畫的方式移動到 0 的位置
		var $body = (window.opera) ? (document.compatMode == "CSS1Compat" ? $('html') : $('body')) : $('html,body');
		$body.animate({
			scrollTop: 0
		}, 600);
		return false;
	});
});
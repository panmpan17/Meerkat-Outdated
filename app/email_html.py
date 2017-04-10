class Email:
	URL = "http://restemailserver.appspot.com"

	REGIST_VALID = """
	<html><head>
	<style>
	div \{
	font-size: 24px;
	}
	div#c4f \{
	top: 0px;
	left: 0px;
	position: absolute;
	width:100%;
	font-size:36px;
	color: white;
	background-color:rgb(43,142,183);}
	button \{
	width:300px;
	height:  100px;
	font-size: 24px;
	color: white;
	background-color:rgb(43,142,183);
	border: 0px;}
	button:hover \{
	background-color: rgb(30,105,138);
	}</style></head><body>
	<center>
	<div id="c4f">Coding For Fun  Email 認證</div><br /><br /><br />
	<div>
	按下面的按鈕, 來啟動你的帳戶: <br /><br />
	<a href="url"><button>啟動我的帳戶</button></a><br /><br />
	或使用以下網址:<br><a href="url">url</a></div></body></center></html>
	"""
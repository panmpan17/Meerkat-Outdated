class Email:
	URL = "http://restemailserver.appspot.com"
	# URL = "http://localhost:8080"

	REGIST_VALID = """
	<html>
	<body>
		<div style="background: url(http://coding4fun.tw/html/images/email_valid.png) no-repeat;width: 720px;height: 680px;padding-top: 186px">
			<div style="color: black;text-align: center;font-size: 48px;">
				{code}
				<br>
				<span style="font-size: 24px;">或直接前往 <a href="http://{url}/active/{code}">http://{url}/active/{code}</a></span>
			</div>
			
		</div>
		
	</body>
	</html>
	"""

	NEWQUESTION = """
	<html>
	<body>
		<h3>{title}</h3>
		<div>{content}</div>
		<br>
		<a href="{url}" style="color:coral">問題</a>
	</body>
	</html>
	"""
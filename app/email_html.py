class Email:
	URL = "http://restemailserver.appspot.com"
	# URL = "http://localhost:8080"

	REGIST_VALID = """
	<html>
	<body>
		<div style="background: url(http://{}/html/images/email_valid.png) no-repeat;width: 720px;height: 680px;color: black;text-align: center;padding-top: 186px;font-size: 48px;">
			{}
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
{
	subject: string,
	summary: text,
	description-video: string[video url],
	description: text,
	price: int,
	link: string[website url],
	image: string[image url],
	time: string,
	id: string,
	info: list[
		{
			class_name: string,
			video: string,
			description: string,
			answer: string,
			buttons: dict
		}
	]
}


(lession title, video url, buttons, answer video url[optional]),
("1-1 Begin", "http://host/vedio-1.mp4", {})
("1-2 Learning", "http://host/vedio-2.mp4", {"1": "http://1"})
("1-3 Begin", "http://host/vedio-3.mp4", {}, "http://host/answer-1.mp4")
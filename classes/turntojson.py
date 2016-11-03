import pprint

id_ = "python_01"
subject_name = "Python"

description_video = "http://www.youtube.com/embed/x9gjp2xYZ3k?rel=0"

description = """\
"""

price = 500

time = "10 堂課"

summary = """\
Python"""

link = ""
image = "class_python.png"

class_list = [
("1-1", "https://storage.googleapis.com/coding4fun-class-video/python-01/1-1.mp4", []),
("1-10", "https://storage.googleapis.com/coding4fun-class-video/python-01/1-10.mp4", []),
]


json = {
	"subject":subject_name,
	"info":[],
	"summary": summary,
	"description-video": description_video,
	"description": description,
	"price":price,
	"link":link,
	"image":image,
	"time": time,
	"id": id_,
	}

# for i in class_list:
# 	a = i[0].split()

# 	unit, _ = map(int, a[0].split("-"))
# 	if len(json["info"]) < unit:
# 		json["info"].append([])

	# class_ = {
	# 	"class_name": i[0],
	# 	"video": i[1],
	# 	"description":"",
	# 	"answer": "",
	# 	"buttons": i[2],
	# 	}
# 	if len(i) == 4:
# 		class_["answer"] = i[3]
# 	json["info"][unit - 1].append(class_)

pprint.pprint(json)
print("\n\n")

change = input("確定要存擋? %s (Y/N)" % (id_ + ".json")).lower()
if change != "y":
	exit()

file = open(id_ + ".json", "w")
file.write(pprint.pformat(json))
file.close()

print("存擋成功")

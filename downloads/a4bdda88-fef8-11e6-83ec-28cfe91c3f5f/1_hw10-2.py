import os

lines = 0
file_count = 0
path = os.getcwd() + "/code/meerkat/"

for dirn, dirns, filens in os.walk(path):
    if (".git" in dirn) or ("__pycache__" in dirn) or ("cherrypy" in dirn) or ("downloads" in dirn):
        continue
    if ("jinja2" in dirn) or ("requests" in dirn) or ("sqlalchemy" in dirn) or ("bootstrap" in dirn):
        continue
    if ("slick" in dirn):
        continue
    for file in filens:
        if file.startswith("_") or file.startswith("jquery"):
            continue
        if file == "six.py" or file == "sb-admin.css" or file == "cherrpy_sa.py":
            continue
        if file == "sha256.js":
            continue
        if file.endswith((".py", ".html", ".css", '.js')):
            file_count += 1
            print(file)
            with open(dirn + "/" + file) as file:
                file_lines = file.read()
                file_lines = file_lines.replace(" ", "")
                file_lines = file_lines.replace("\t", "")
                file_lines = file_lines.split("\n")
                fl = 0
                for l in file_lines:
                    if l.startswith("#") or l.startswith("//") or l.startswith("/*") or l.startswith("<!--"):
                        continue
                    if l != "":
                        lines += 1
                        fl += 1
                print(fl)
print()
print("檔案數", file_count)
print("行數", lines)
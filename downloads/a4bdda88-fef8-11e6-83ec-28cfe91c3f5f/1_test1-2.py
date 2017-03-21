from flask import Flask
from flask import jsonify

from random import randint
import requests

app = Flask(__name__)

url = "http://www.manythings.org/vocabulary/lists/l/words.php?f=3esl.{}"
a2z = "abcdefghijklmnopqrstuvwxyz"

def load_vocabularies():
    vocabularies = {}
    for i in range(1, 24):
        start = a2z[i - 1]
        vocabularies[start] = []
        if i < 10:
            r = requests.get(url.format("0" + str(i)))
        else:
            r = requests.get(url.format(i))

        text = r.text
        findstart = text.find("<li>")
        while findstart != -1:
            findsend = text.find("</li>", findstart)

            word = text[findstart + 4:findsend]
            word = word.replace(".", "")
            word = word.replace("'", "")
            vocabularies[start].append(word)

            text = text[findsend:]
            findstart = text.find("<li>")

    r = requests.get(url.format("24"))
    text = r.text
    findstart = text.find("<li>")
    while findstart != -1:
        findsend = text.find("</li>", findstart)

        word = text[findstart + 4:findsend]
        if word[0] not in vocabularies.keys():
            vocabularies[word[0]] = []
        vocabularies[word[0]].append(word)

        text = text[findsend:]
        findstart = text.find("<li>")

    return vocabularies

@app.route("/")
def index():
    return "hello"

@app.route("/word/<word>")
def word(word):
    return "<br>".join(vocabularies[word[0]])

@app.route("/words")
def words():
    return jsonify(vocabularies)

if __name__ == "__main__":
    # vocabularies = load_vocabularies()
    vocabularies = {"a": ["a"]}
    app.run()
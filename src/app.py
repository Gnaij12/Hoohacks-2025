from flask import Flask, render_template, request
import os

template_dir = os.path.abspath("./templates")
app = Flask(__name__, template_folder="../templates/", static_folder="../static/")


@app.route("/", methods=["GET"])
def main_page() -> str:
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
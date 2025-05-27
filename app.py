from flask import Flask, request, render_template
from src.transpiler import transpile

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    output = ""
    error = ""
    if request.method == 'POST':
        code = request.form['code']
        source_lang = request.form['source_lang']
        target_lang = request.form['target_lang']
        try:
            output = transpile(code, source_lang, target_lang)
        except Exception as e:
            error = str(e)
    return render_template('index.html', output=output, error=error)

if __name__ == '__main__':
    app.run(debug=True)
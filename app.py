from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/apresentacao")
def apresentacao():
    return render_template("apresentacao.html")

@app.route("/cadastro")
def cadastro():
    return render_template("cadastro.html")

@app.route("/chat")
def chat():
    return render_template("chat.html")

@app.route("/contato")
def contato():
    return render_template("contato.html")

@app.route("/contribuicao")
def contribuicao():
    return render_template("contribuicao.html")

@app.route("/cursos")
def cursos():
    return render_template("cursos.html")

@app.route("/feed")
def feed():
    return render_template("feed.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/perfil")
def perfil():
    return render_template("perfil.html")

@app.route("/politica")
def politica():
    return render_template("politica.html")

@app.route("/sobre")
def sobre():
    return render_template("sobre.html")

@app.route("/termos")
def termos():
    return render_template("termos.html")

@app.route("/vagas")
def vagas():
    return render_template("vagas.html")

if __name__ == '__main__':
    app.run(debug=True)

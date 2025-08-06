import os
import secrets
import json
from uuid import uuid4
from flask import Flask, redirect, render_template, send_from_directory, flash, url_for, request, session, jsonify
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from wtforms import (
    StringField,
    SubmitField,
    TextAreaField,
    PasswordField,
)
from wtforms.validators import DataRequired, Length, Email, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from database import configurar_banco, db, Post, User, Profile
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)

# --- Configuração do Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

csrf = CSRFProtect(app)
db = configurar_banco(app)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = secrets.token_urlsafe(64)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Formulários
class PostarForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired(), Length(min=3, max=255)])
    imagem = FileField('Imagem', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'svg'], 'Apenas imagens são permitidas!')])
    descricao = TextAreaField('Descrição', validators=[DataRequired(),])
    submit = SubmitField('Postar')

class CadastroForm(FlaskForm):
    username = StringField('Nome', validators=[DataRequired(), Length(min=3, max=255)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(min=3, max=255)])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6, max=255)])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password', message='As senhas devem ser iguais.')])
    submit = SubmitField('Cadastrar')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(min=3, max=255)])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6, max=255)])
    submit = SubmitField('Login')

class ProfileForm(FlaskForm):
    bio = TextAreaField('Biografia', validators=[Length(max=500)])
    profile_pic = FileField('Foto de Perfil', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Apenas imagens são permitidas!')])
    submit = SubmitField('Salvar Perfil')

# Rotas
@app.route('/')
def index():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template("index.html", posts=posts)

@app.route('/postar', methods=['GET', 'POST'])
@login_required
def postar():
    form = PostarForm()
    if form.validate_on_submit():
        imagem_filename = None # Inicializa com None
        if form.imagem.data and hasattr(form.imagem.data, 'filename') and form.imagem.data.filename:
            arquivo = form.imagem.data
            nome_arquivo_seguro = secure_filename(arquivo.filename)
            # Gerar um nome de arquivo único para evitar conflitos
            imagem_filename = f'{uuid4().hex}_{nome_arquivo_seguro}'
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], imagem_filename)
            arquivo.save(caminho)
        else:
            # Se nenhuma imagem foi enviada, use uma imagem padrão ou defina como nulo no banco de dados
            imagem_filename = 'default_post.jpg' # Ou None, dependendo da sua lógica

        post = Post(
            title=form.title.data,
            imagem=imagem_filename, # Usa o nome do arquivo (ou padrão/None)
            descricao=form.descricao.data,
            author=current_user
        )
        db.session.add(post)
        db.session.commit()
        flash("Postagem criada com sucesso!", "success")
        return redirect(url_for('feed'))
    return render_template('postar.html', form=form)

@app.route('/post_delete/<string:post_id>', methods=['GET', 'POST'])
@login_required
def post_delete(post_id):
    post = Post.query.get_or_404(post_id)
    # Garante que apenas o autor pode deletar a postagem
    if post.author != current_user:
        flash("Você não tem permissão para deletar esta postagem.", "danger")
        return redirect(url_for('perfil', user_id=current_user.id))

    # Deleta o arquivo de imagem associado se não for a imagem padrão
    if post.imagem and post.imagem != 'default.jpg':
        caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], post.imagem)
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)

    db.session.delete(post)
    db.session.commit()
    flash("Postagem deletada com sucesso!", "success")
    return redirect(url_for('perfil', user_id=current_user.id))
@app.route('/editar_post/<string:post_id>', methods=['GET', 'POST'])
@login_required
def editar_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author != current_user:
        flash("Você não tem permissão para editar esta postagem.", "danger")
        return redirect(url_for('perfil', user_id=current_user.id))

    form = PostarForm()

    if request.method == 'GET':
        form.title.data = post.title
        form.descricao.data = post.descricao
    elif form.validate_on_submit():
        post.title = form.title.data
        post.descricao = form.descricao.data

        if form.imagem.data and hasattr(form.imagem.data, 'filename') and form.imagem.data.filename:
            if post.imagem and post.imagem != 'default_post.jpg':
                old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], post.imagem)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)

            arquivo = form.imagem.data
            nome_arquivo_seguro = secure_filename(arquivo.filename)
            new_image_filename = f'{uuid4().hex}_{nome_arquivo_seguro}'
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], new_image_filename)
            arquivo.save(caminho)
            post.imagem = new_image_filename

        db.session.commit()
        flash("Postagem atualizada com sucesso!", "success")
        return redirect(url_for('perfil', user_id=current_user.id))

    return render_template('postar.html', form=form, post=post) # Passa o objeto post para o template



@app.route("/apresentacao")
def apresentacao():
    return render_template("apresentacao.html")

@app.route("/cadastro", methods=['GET', 'POST'])
def cadastro():
    form = CadastroForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Este e-mail já está cadastrado. Por favor, use outro.", "danger")
            return redirect(url_for('cadastro'))

        if User.query.filter_by(username=form.username.data).first():
            flash("Este nome de usuário já está cadastrado. Por favor, use outro.", "danger")
            return redirect(url_for('cadastro'))

        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')

        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()
        flash("Cadastro realizado com sucesso! Faça login para continuar.", "success")
        return redirect(url_for('index'))

    return render_template("cadastro.html", form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash(f"Login bem-sucedido, {user.username}!", "success")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash("Login falhou. Verifique seu e-mail e senha.", "danger")

    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você foi desconectado com sucesso.", "success")
    return redirect(url_for('index'))

@app.route("/perfil/<string:user_id>")
def perfil(user_id):
    user = User.query.get_or_404(user_id)
    user_profile = Profile.query.filter_by(user_id=user.id).first()
    user_posts = Post.query.filter_by(user_id=user.id).order_by(Post.data_criacao.desc()).all()
    # Pegar o profile
    name = user.username
    
    return render_template("perfil.html", user=user, user_profile=user_profile, name=name, user_posts=user_posts)

@app.route("/perfil")
@login_required
def meu_perfil():
    return redirect(url_for('perfil', user_id=current_user.id))

@app.route("/criar_perfil", methods=['GET', 'POST'])
@login_required
def criar_perfil():
    form = ProfileForm()
    user_profile = Profile.query.filter_by(user_id=current_user.id).first()

    if user_profile and request.method == 'GET':
        form.bio.data = user_profile.bio

    if form.validate_on_submit():
        # Inicializa profile_pic_filename com o valor existente ou padrão
        profile_pic_filename = user_profile.profile_pic if user_profile else 'default.jpg'

        # Verifica se um novo arquivo foi enviado e se ele tem um nome de arquivo válido
        if form.profile_pic.data and hasattr(form.profile_pic.data, 'filename') and form.profile_pic.data.filename:
            arquivo = form.profile_pic.data
            nome_arquivo_seguro = secure_filename(arquivo.filename)
            profile_pic_filename = f'{uuid4().hex}_{nome_arquivo_seguro}'
            caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], profile_pic_filename)
            arquivo.save(caminho_arquivo)

            # Se houver um perfil existente e uma foto antiga que não seja a padrão, a remove
            if user_profile and user_profile.profile_pic != 'default.jpg':
                old_pic_path = os.path.join(app.config['UPLOAD_FOLDER'], user_profile.profile_pic)
                if os.path.exists(old_pic_path):
                    os.remove(old_pic_path)
        # Se nenhum novo arquivo foi enviado, profile_pic_filename mantém seu valor inicial (existente ou padrão)

        if user_profile:
            user_profile.bio = form.bio.data
            user_profile.profile_pic = profile_pic_filename
            flash("Perfil atualizado com sucesso!", "success")
        else:
            new_profile = Profile(
                user_id=current_user.id,
                bio=form.bio.data,
                profile_pic=profile_pic_filename
            )
            db.session.add(new_profile)
            flash("Perfil criado com sucesso!", "success")

        db.session.commit()
        return redirect(url_for('perfil', user_id=current_user.id))

    return render_template("criar_perfil.html", form=form, user_profile=user_profile)

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

@app.route("/feed", methods=['GET', 'POST'])
def feed():
    posts = Post.query.all()
    return render_template("feed.html", posts=posts)

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

@app.route('/uploads/<path:arquivo>')
def arquivocarregado(arquivo):
    return send_from_directory(app.config['UPLOAD_FOLDER'], arquivo)

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from uuid import uuid4
from flask_login import UserMixin
db = SQLAlchemy()

def configurar_banco(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("Banco de dados criado com sucesso!")
        return db

def gerar_uuid():
    return uuid4().hex

class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.String(32), primary_key=True, default=gerar_uuid)
    title = db.Column(db.String(100), nullable=False)
    imagem = db.Column(db.String(), nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.String(32), db.ForeignKey('user.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.now)

    # Relacionamento com a tabela 'user' para acessar os dados do autor do post
    author = db.relationship('User', backref=db.backref('posts', lazy=True))

    def __init__(self, title, imagem, descricao, author):
        self.title = title
        self.imagem = imagem
        self.descricao = descricao
        self.author = author

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.String(32), primary_key=True, default=gerar_uuid)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    DateCreate = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

class Profile(db.Model):
    __tablename__ = 'profile'
    id = db.Column(db.String(32), primary_key=True, default=gerar_uuid)
    # user_id é a chave estrangeira para o usuário, e é único para cada perfil
    user_id = db.Column(db.String(32), db.ForeignKey('user.id'), nullable=False, unique=True)
    bio = db.Column(db.Text, nullable=True)
    profile_pic = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relacionamento com a tabela 'user' para acessar o perfil a partir do usuário
    user = db.relationship('User', backref=db.backref('profile', uselist=False))

    def __init__(self, user_id, bio, profile_pic):
        self.user_id = user_id
        self.bio = bio
        self.profile_pic = profile_pic
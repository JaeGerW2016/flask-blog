#! -*- coding: utf-8 -*-
from . import db, login_manager
from flask_login import UserMixin, AnonymousUserMixin
from markdown import markdown
from datetime import datetime


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16))
    users = db.relationship('User', backref='role')

    @staticmethod
    def seed():
        db.session.add_all(map(lambda r: Role(name=r), ['Guests', 'Administrators']))
        db.session.commit()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16))
    email = db.Column(db.String(16))
    password = db.Column(db.String(16))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    posts = db.relationship('Post', backref='author')
    comments = db.relationship('Comment', backref='author')

    locale = db.Column(db.String(16), default='zh')

    @staticmethod
    def on_created(target, value, oldvalue, initiator):
        target.role = Role.query.filter_by(name='Guests').first()


db.event.listen(User.name, 'set', User.on_created)


class AnonymousUser(AnonymousUserMixin):
    @property
    def locale(self):
        return 'zh'

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(16))
    body = db.Column(db.String(16))
    body_html = db.Column(db.String(16))
    created = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    comments = db.relationship('Comment', backref='post')
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

    @staticmethod
    def on_body_change(target, value, oldvalue, initianor):
        if value is None or (value is ''):
            target.body_html = ''
        else:
            target.body_html = markdown(value)

    def delete(self):
        comments = self.comments
        for comm in comments:
            db.session.delete(comm)
        db.session.delete(self)
        db.session.commit()


db.event.listen(Post.body, 'set', Post.on_body_change)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(64))
    created = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.Unicode(128), unique=True)
    posts = db.relationship('Post', backref='category', lazy='dynamic')

    @staticmethod
    def add_categorys():
        categorys = [
            u'博客开发',
            u'生活点滴',
            u'默认分类'
        ]
        for c in categorys:
            category = Category.query.filter_by(category=c).first()
            if category is None:
                category = Category(category=c)
            db.session.add(category)
        db.session.commit()

    def __repr__(self):
        return '<Category %r>' % self.category

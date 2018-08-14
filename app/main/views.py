# -*- coding: utf-8 -*-

from flask import render_template, request, flash, redirect, url_for, current_app, abort, session
from . import main
from .. import db
from ..models import Post, Comment
from flask_login import login_required, current_user
from .forms import CommentForm, PostForm
from flask_babel import gettext as _


@main.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@main.route('/')
def index():
    page_index = request.args.get('page', 1, type=int)
    query = Post.query.order_by(Post.created.desc())
    pageination = query.paginate(page_index, per_page=20, error_out=False)
    posts = pageination.items

    return render_template('index.html', title=_(u'欢迎K的Blog'),
                           posts=posts,
                           pageination=pageination)


@main.route('/about')
def about():
    return render_template('about.html', title=u'关于')


@main.route('/posts/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)

    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(author=current_user,
                          body=form.body.data,
                          post=post)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been published.')
        session['body'] = form.body.data
        return redirect(url_for('.post', id=post.id))

    return render_template('posts/detail.html', title=post.title, form=form, post=post, body=session.get('body'))


@main.route('/edit', methods=['GET', 'POST'])
@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id=0):
    form = PostForm()
    if id == 0:
        post = Post(author_id=current_user.id)
    else:
        post = Post.query.get_or_404(id)

    if form.validate_on_submit():
        post.body = form.body.data
        post.title = form.title.data

        db.session.add(post)
        db.session.commit()

        return redirect(url_for('.post', id=post.id))

    form.title.data = post.title
    form.body.data = post.body

    title = _(u'添加新文章')
    if id > 0:
        title = _(u'编辑 - %(title)', title=post.title)

    return render_template('posts/edit.html', title=title, form=form, post=post)

@main.route('/posts/delete/<int:id>')
@login_required
def post_delete(id):
    post = Post.query.get_or_404(id)
    if current_user.id != post.author_id:
        about(403)
    post.delete()
    flash(u'文章已删除')
    return redirect(url_for('.index'))


@main.route('/shutdown')
def shutdown():
    if not current_app.testing:
        abort(404)

    shoutdown = request.environ.get('werkzeug.server.shutdown')
    if not shoutdown:
        abort(500)

    shutdown()
    return u'正在关闭服务端进程...'

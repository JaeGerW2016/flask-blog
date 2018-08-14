from flask_script import Manager, Shell
from app import create_app, db
from app.models import User, Role, Post, Comment
from flask_migrate import Migrate, MigrateCommand, upgrade

app = create_app('production')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command("db", MigrateCommand)


@manager.command
def dev():
    import os
    from livereload import Server
    live_server = Server(app.wsgi_app)
    for root, dirs, files in os.walk(os.getcwd()):
        for name in files:
            filth = os.path.join(root, name)
            live_server.watch(filth)
    live_server.server(open_url=False)


@manager.command
def test():
    import unittest
    tests = unittest.TestLoader().discover('test')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def deploy():
    upgrade()
    Role.seed()


@manager.command
def forged():
    from forgery_py import basic, lorem_ipsum, name, internet, date
    from random import randint

    db.drop_all()
    db.create_all()

    Role.seed()

    guests = Role.query.first()

    def generate_comment(func_author, func_post):
        return Comment(body=lorem_ipsum.paragraph(),
                       created=date.date(past=True),
                       author=func_author(),
                       post=func_post())

    def generate_post(func_author):
        return Post(title=lorem_ipsum(),
                    body=lorem_ipsum.paragraph(),
                    created=date.date(),
                    author=func_author())

    def generate_user():
        return User(name=internet.user_name(),
                    email=internet.email_address(),
                    passsword=basic.text(6, at_least=6, spaces=False),
                    role=guests)

    users = [generate_user() for i in range(0, 5)]
    db.session.commit()

    random_user = lambda: users[randint(0, 4)]

    posts = [generate_post(random_user) for i in range(0, randint(50, 200))]
    db.session.add_all(posts)

    random_post = lambda: posts[randint(0, len(posts) - 1)]

    comments = [generate_comment(random_user, random_post) for i in range(0, randint(2, 100))]
    db.session.add_all(comments)

    db.session.commit()


if __name__ == "__main__":
    manager.run()

from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:password@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'this_is_my_secret_key'

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(50))
    body = db.Column(db.String(250))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

class User(db.Model):

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(25), unique = True)
    password = db.Column(db.String(25))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password

@app.before_request
def require_login():
    allowed_routes = ['login', 'blog', 'index', 'signup']

    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        login_username_error = ""

        if user and user.password == password:
            session['username'] = username
            #flash("Welcome back, " + username)
            return redirect('/newpost')
        else:
            login_error = "No user by this username or password is incorrect"
            return render_template("login.html", login_error=login_error)

    return render_template('login.html')

    if request.method == 'GET':
        return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    username_error = ""
    password_error = ""
    verify_password_error = ""
    user_exists_error = ""

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify_password = request.form['verify_password']

        if len(username) < 3 or len(username) > 20:
            username_error = "Please enter a username between 3 and 20 characters"
            return render_template("signup.html", username_error=username_error)

        if " " in username:
            username_error = "Username cannot contain spaces"
            return render_template("signup.html", username_error=username_error)

        if len(password) < 3 or len(password) > 20:
            password_error = "Please enter a password between 3 and 20 characters"
            return render_template("signup.html", password_error=password_error)

        if " " in password:
            password_error = "Password cannot contain spaces"
            return render_template("signup.html", password_error=password_error)

        if password != verify_password:
            verify_password_error = "Password and verify password must match"
            return render_template("signup.html", verify_password_error=verify_password_error)

        existing_user = User.query.filter_by(username=username).first()
        if not existing_user:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')
        else:
            user_exists_error = "Username already exists"
            return render_template("signup.html", user_exists_error=user_exists_error)

    return render_template('signup.html', username_error=username_error
                                        , password_error=password_error
                                        , verify_password_error=verify_password_error)

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')

@app.route('/newpost', methods=['GET', 'POST'])
def add_blog():
    if request.method == 'GET':
        return render_template('newpost.html')

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        title_error = ""
        body_error = ""

        if title == "":
            title_error = "Please enter a title."
        
        if body == "":
            body_error = "Please enter the body."

        if not title_error and not body_error:
            owner = User.query.filter_by(username=session['username']).first()
            new_blog = Blog(title, body, owner)
            db.session.add(new_blog)
            db.session.commit()
            query_param_url = "/blog?id=" + str(new_blog.id)
            return redirect(query_param_url)
        else:
            return render_template('newpost.html', title_error=title_error
                                                 , body_error=body_error)

@app.route('/blog', methods=['POST', 'GET'])
def get_individual_blog():
    owner_id = request.args.get("user")

    if (owner_id):
        blogs = Blog.query.filter_by(owner_id=owner_id)
        return render_template('singleUser.html', title="Authors' Posts", blogs=blogs)
    blog_id = request.args.get("id")
    if (blog_id):
        blog = Blog.query.get(blog_id)
        return render_template('postblog.html', page_title="Blog Entry", blog=blog)

    sort_type = request.args.get("sort")

    if sort_type == "newest":
        blogs = Blog.query.order_by(Blog.created.desc()).all()
    else:
        blogs = Blog.query.all()

        return render_template('blog.html', blogs=blogs)

@app.route('/')
def index():
    users = User.query.order_by(User.id.desc()).all()
    return render_template('index.html', title="Blog posts by Author", users=users)

if __name__ == '__main__':
    app.run()
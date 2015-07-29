"""
Welcome to SDN!

By Jay Ravaliya
"""

# establish all imports
import os
from flask import Flask, render_template, request, redirect, url_for, session
from model import Users, Projects, db
import hashlib
from functools import wraps
from flask.ext.assets import Environment, Bundle

# add app and config
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'this_should_be_configured')
assets = Environment(app)

###
# Functions
###

### login_required wrapper
### Restricts specific pages to users-only.
def login_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if 'logged_in_id' not in session.keys():
			return redirect('/login')

		return f(*args, **kwargs)
	return decorated_function

### return_current_user
### Returns current user as a Users object
def return_current_user():
	if 'logged_in_id' not in session.keys():
		return False
	else:
		return Users.query.filter_by(id=session['logged_in_id']).first()		


###
# Assets
###

css = Bundle('css/styles.css', output = 'get/packed.css')
assets.register('css_all', css)

###
# Routing for your application.
###

### Home route. Will display welcome page, links to Login or Register.
 
@app.route('/')
def home():
	user = return_current_user()
	if user == False:
		return "No one is logged in."
	else:
		return user.email

### Login route. Will display login form, or handle the login process for the user.
### Once logged in, user id is stored in a session variable.

@app.route('/login', methods=['GET','POST'])
def login():
	if request.method == 'GET':
		return render_template('login.html', title="Log In")

	elif request.method == 'POST':
		un = request.form['username']
		pw = hashlib.md5(request.form['password']).hexdigest()
		
		user = Users.query.filter_by(username = un).filter_by(password = pw).first()
		if not user:
			return render_template('login.html', error = "User not found!")
		
		else:
			session['logged_in_id'] = user.id
			return redirect('/')

	else:
		return render_template('login.html', error = "Invalid request method!")

### Register route. Will allow users to register for the site.

@app.route('/register', methods=['GET','POST'])
def register():
	if request.method == 'GET':
		return render_template('register.html', title="Register")
	elif request.method == 'POST':
		un = request.form['username']
		pw = hashlib.md5(request.form['password']).hexdigest()
		em = request.form['email']
		if not Users.query.filter_by(username = un).filter_by(email = em).first():
			user = Users(un, pw, em)
			db.session.add(user)
			db.session.commit()	
			session['logged_in_id'] = user.id
			redirect('/')	
		else:
			return render_template('register.html', title="Register", error_message="This username already exists!")

### Projects route. Will list out all projects currently offered.

@app.route('/projects', methods=['GET'])
@login_required
def projects():
	return "Under construction!"

### About route. Will take user to an "About Us" page.

@app.route('/about', methods=['GET'])
def about():
	return "By Jay Ravaliya. Details under construction!"

### Profile route. Will generate a profile of the current user.

@app.route('/profile', methods=['GET'])
def profile():
	return "My profile!"

### Logout route. Will logout the user. More technically, will remove ID from session/cookies.

@app.route('/logout', methods=['GET'])
def logout():
	session.pop('logged_in_id', None)
	return redirect('/')

###
# Add headers to both force latest IE rendering engine or Google Frame,
# and also to cache the rendered page for 10 minutes.
###

@app.after_request
def add_header(response):
	response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
	response.headers['Cache-Control'] = 'public, max-age=600'
	return response

###
# Error Handling
###

@app.errorhandler(404)
def page_not_found(error):
	"""Custom 404 page."""
	return render_template('404.html'), 404

###
# Run!
###

if __name__ == '__main__':
	app.run(debug=True)

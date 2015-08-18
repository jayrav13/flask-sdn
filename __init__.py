"""
Welcome to SDN!

By Jay Ravaliya
"""

# establish all imports
import os
from flask import Flask, render_template, request, redirect, url_for, session
from model import Users, Projects, ProjectComments, db
import hashlib
from functools import wraps
from flask.ext.assets import Environment, Bundle

# add app and config
app = Flask(__name__)
app.config['SECRET_KEY'] = "Testing-Secret-Key" 
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

### validate_credentials
### Confirms that Username and Password are valid.
def validate_credentials(input):
	if input.isalnum:
		if len(input) >= 8 and len(input) <= 16:
			return True
		else:
			return False
	else:
		return False


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
	return render_template('home.html', title="Welcome", user=user)

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
			return render_template('login.html', title="Log In",  error_message = "Invalid credentials - please try again!")
		
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
	
		if not Users.query.filter_by(email=em).filter_by(username=un).first():
			if validate_credentials(un) == True and validate_credentials(request.form['password']) == True: 
				user = Users(un, pw, em)
				db.session.add(user)
				db.session.commit()
		
				session['logged_in_id'] = user.id
				return redirect('/')	
			
			else:
				return render_template('register.html', title="Register", error_message="Username and Password must be alphanumeric and between 8 and 16 characters each!")

		else:
			return render_template('register.html', title="Register", error_message="This username or email already exists!")
	else:
		return render_template('register.html', title='Register', error_message="Invalid request method!")

### Projects route. Will list out all projects currently offered.

@app.route('/projects', methods=['GET','POST'])
@login_required
def projects():
	user = return_current_user()

	if request.method == 'POST':
		if request.form['title'] and request.form['description']:
			project = Projects(request.form['title'], request.form['description'])
			user.projects.append(project)
			db.session.commit()
	
		return redirect('/projects')

	elif request.method == 'GET':
		if 'clear-page' in request.args:
			return redirect('/projects')
		elif 'query' in request.args:
			projects = Projects.query.filter(Projects.title.like('%'+request.args['query']+'%')).order_by(Projects.timestamp.desc()).all()
			
		else:
			projects = Projects.query.order_by(Projects.timestamp.desc()).all()			

		return render_template('projects.html', title="Projects", user=user, projects=projects)

@app.route('/projects/details', methods=['GET','POST'])
def projects_details():
	if 'id' in request.args:
		project = Projects.query.filter_by(id=request.args['id']).first()
		if not project:
			return redirect('/projects')
		else:
			user = return_current_user()
			comment = ProjectComments(user, project, "test-comment")
			db.session.commit()
			return render_template('details.html', title="Details", user=user, project=project)			
	
	else:
		return redirect('/projects')

@app.route('/projects/delete', methods=['GET'])
def projects_delete():
	if 'id' in request.args:
		project = Projects.query.filter_by(id=request.args['id']).first()
		user = return_current_user()
		if project and project.user_id == user.id:
			db.session.delete(project)
			db.session.commit()
		
	return redirect('/projects')

### About route. Will take user to an "About Us" page.

@app.route('/about', methods=['GET'])
def about():
	return "By Jay Ravaliya. Details under construction!"

### Profile route. Will generate a profile of the current user.

@app.route('/profile', methods=['GET'])
@login_required
def profile():
	if "id" in request.args:
		user = Users.query.filter_by(id=request.args['id']).first()		

		if user:
			return render_template('userprofile.html', title=user.username, user=user)
		else:
			return redirect("/")
	else:
		user = return_current_user()
		return render_template('userprofile.html', title=user.username, user=user)
		

@app.route('/users', methods=['GET'])
@login_required
def users():
	return "Users"

### Logout route. Will logout the user. More technically, will remove ID from session/cookies.

@app.route('/logout', methods=['GET'])
def logout():
	session.pop('logged_in_id', None)
	return redirect(url_for('home'))
	
###
# Add headers to both force latest IE rendering engine or Google Frame,
# and also to cache the rendered page for 10 minutes.
###

@app.after_request
def add_header(response):
	response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
	response.headers['Cache-Control'] = 'public, max-age=0'
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
	app.run(debug=True, host="45.33.69.6")

"""
Welcome to SDN!

By Jay Ravaliya
"""

# establish all imports
import os
from flask import request_finished, jsonify, Flask, render_template, request, redirect, url_for, session, make_response
from model import Users, Projects, ProjectComments, Messages, db 
import hashlib
import HTMLParser
from functools import wraps
from flask.ext.assets import Environment, Bundle
from flask.ext.mail import Mail, Message
from sqlalchemy import or_, desc

# add app and config
app = Flask(__name__)
app.config['SECRET_KEY'] = "Testing-Secret-Key" 
assets = Environment(app)

app.config['SQLALCHEMY_POOL_RECYCLE'] = 499
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 20

h = HTMLParser.HTMLParser()

###
# Functions
###

### login_required wrapper
### Restricts specific pages to users-only.
def login_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		db.session.commit()
		if 'logged_in_id' not in session.keys():
			return redirect('/login')
		
		return f(*args, **kwargs)
	return decorated_function

### return_current_user
### Returns current user as a Users object if the user is logged in.
def return_current_user():
	db.session.commit()
	if 'logged_in_id' not in session.keys():
		return False
	else:
		return Users.query.filter_by(id=session['logged_in_id']).first()		

### validate_credentials
### Confirms that Username and Password are valid.
def validate_credentials(input):
	if input.isalnum():
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
			return render_template('login.html', title="Log In",  message_content = "Invalid credentials - please try again!", message_type="danger")
		
		else:
			session['logged_in_id'] = user.id
			return redirect('/')

	else:
		return render_template('login.html', message_content = "Invalid request method!", message_type="danger")

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
				if request.form['password'] == request.form['confirm-password']:	
					user = Users(un, pw, em)
					db.session.add(user)
					db.session.commit()

					session['logged_in_id'] = user.id
					return redirect('/')	
				else:
					return render_template('register.html', title='Register', error_message="Password's don't match! Try again!")
			else:
				return render_template('register.html', title="Register", error_message="Username and Password must be alphanumeric from 8-16 characters.")
		else:
			return render_template('register.html', title="Register", error_message="This username or email already exists!")
	else:
		return render_template('register.html', title='Register', error_message="Invalid request method!")

### Projects route. Will list out all projects currently offered.

@app.route('/projects', methods=['GET','POST'])
@login_required
def projects():
	user = return_current_user()
	messages = Messages.query.filter_by(to_id=user.id).all()

	if request.method == 'POST':
		if request.form['title'] and request.form['description']:
			project = Projects(request.form['title'], request.form['description'])
			if project.title != None and project.description != None:
				user.projects.append(project)
				db.session.commit()
	
		return redirect('/projects')

	elif request.method == 'GET':
		if 'clear-page' in request.args:
			return redirect('/projects')
		elif 'query' in request.args:
			projects = Projects.query.filter(or_(Projects.title.like('%'+request.args['query']+'%'), Projects.description.like('%'+request.args['query']+'%'))).order_by(Projects.timestamp.desc()).all()
			
		else:
			projects = Projects.query.order_by(Projects.timestamp.desc()).all()			

		return render_template('projects.html', title="Projects", user=user, projects=projects, messages=messages)

### Projects Details route. Will load details about a project, including comments.

@app.route('/projects/details', methods=['GET','POST'])
@login_required
def projects_details():
	user = return_current_user()
	
	if request.method == "GET":
		if 'id' in request.args:
			project = Projects.query.filter_by(id=request.args['id']).first()
			return render_template('details.html', user=user, project=project, title=project.title)
		else:
			return redirect('/projects')
	
	elif request.method == "POST":	
		if 'comment-content' in request.form:
			project = Projects.query.filter_by(id=request.form['project_id']).first()
			if project is not None:
				user = return_current_user()
				comment = ProjectComments(request.form['comment-content'], user, project)
				if comment is not None and comment.comment is not None:
					db.session.add(comment)
					db.session.commit()
	
				return redirect('/projects/details?id=' + request.form['project_id'])				
			else:
				return redirect('/projects')		
		elif 'project_id' in request.form and 'comment_id' in request.form:
			comment = ProjectComments.query.filter_by(id=request.form['comment_id']).filter_by(project_id=request.form['project_id']).first()
			if comment and comment.user_id == user.id:
				db.session.delete(comment)
				db.session.commit()

			return redirect('/projects/details?id=' + request.form['project_id'])
		else:
			return redirect('/projects')
	
	else:
		return redirect('/')	


@app.route('/projects/delete', methods=['GET'])
@login_required
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
	user = return_current_user()
	return render_template('about.html', user=user, title="About")
	
### Profile route. Will generate a profile of the current user.

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
	user = return_current_user()
	if request.method == "GET":
		if "id" in request.args:
			profile_user = Users.query.filter_by(id=request.args['id']).first()		
		
			if profile_user:
				return render_template('userprofile.html', title=profile_user.username, profile_user=profile_user, user=user)
			else:
				return redirect("/profile")
		else:
			return render_template('userprofile.html', title=user.username, profile_user=user, user=user)
	elif request.method == "POST":
		if not request.form['email']:
			return redirect('/profile')
		else:
			user.password = hashlib.md5(request.form['password']).hexdigest() if validate_credentials(request.form['password']) else user.password
			user.email = request.form['email']
			user.github_link = request.form['github'] if len(request.form['github']) > 0 else None
			user.facebook_link = request.form['facebook'] if len(request.form['facebook']) > 0 else None
			user.linkedin_link = request.form['linkedin'] if len(request.form['linkedin']) > 0 else None
			user.twitter_link = request.form['twitter'] if len(request.form['linkedin']) > 0 else None

			if 'public_profile_checkbox' in request.form:
				user.public_profile = 1
			else:
				user.public_profile = 0

			db.session.commit()				
			
			return redirect('/profile')

### Logout route. Will logout the user. More technically, will remove ID from session/cookies.

@app.route('/logout', methods=['GET'])
def logout():
	session.pop('logged_in_id', None)
	return redirect(url_for('home'))

### Manage Password:
@app.route('/password', methods=['GET', 'POST'])
def manage_password():
	### All possibilities for GET:
	# No Token - let user enter email to reset.
	# Valid Token - allow user to enter new password.
	# Invalid token - render login form and yell at user.
	if request.method == 'GET':
		if 'token' not in request.args:
			return render_template('forgot-password.html', title="Forgot Password")
		else:
			user = Users.query.filter_by(forgot_token=request.args['token']).first()
			if user:
				return render_template('new-password.html', title="Enter New Password", user=user, message_type="success", message_content="Hey " + user.username + ", enter a new password.", token=request.args['token'])
			else:
				return render_template('login.html', title="Log In", message_content="Invalid Token!", message_type="danger")

	### All Possibilities for POST:
	# forgot-password: User has entered email address for which to retrieve forgotten password.
	# new-password: User has entered a new password and is looking to have it updated.
	# Any other POST request: redirect to login.
	else:
		if 'forgot-password' in request.form:			
			user = Users.query.filter_by(email=request.form['forgot-password']).first()
			if not user:
				return render_template('forgot-password.html',title="Forgot Password",message_content = "Sorry, didn't find your email.", message_type="danger")
			else:
				user.send_forgot_password_email(request.url_root)
				return render_template('forgot-password.html', title="Forgot Password", message_content="Check your email for a link via which you can reset your password!", message_type="success")
		### CRITICAL
		# If a new password arrives, user object is generated using the value of the Submit button which will be the token.
		# As long as that user exists, new password reset will proceed.		
		elif 'new-password' in request.form:
			user = Users.query.filter_by(forgot_token=request.form['new-password-submit']).first()
			if not user:
				return render_template('login.html', title="Log In", message_content="Error with token.", message_type="danger")
			else:
				if validate_credentials(request.form['new-password']):
					user.password = hashlib.md5(request.form['new-password'].encode('utf-8')).hexdigest()
					user.forgot_token = None
					user.forgot_timeout = None
			
					db.session.commit()

					return render_template('login.html', title="Log In", message_type="danger", message_content="Password successfully changed! Log In with new password to continue.")
				else:
					return render_template('new-password.html',title="New Password",message_type="danger",message_content="Invalid Password!")	
		else:
			return redirect('/password')

@app.route('/users', methods=['GET'])
@login_required
def users():
	user = return_current_user()
	users = Users.query.filter_by(public_profile=1).all()
	return render_template('users.html', user=user, users=users, title="Users")


@app.route('/messages', methods=['GET','POST'])
@login_required
def messages():
	user = return_current_user()
	messages = Messages.query.filter(or_(Messages.from_id==user.id, Messages.to_id==user.id)).order_by(desc(Messages.timestamp)).all()
	return render_template('messages.html', title="Messages", user=user, messages=messages)

@app.template_filter('unread_messages')
def unread_messages(value, filt=0):
	output = []
	for messages in value:
		if messages.unread == filt:
			output.append(messages)

	return output


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

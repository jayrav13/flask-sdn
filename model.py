from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, ForeignKey, String, Column, or_
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.associationproxy import association_proxy
from secret import DB_KEY, GMAIL_USERNAME, GMAIL_PASSWORD
from flask.ext.mail import Mail, Message
import time
import hashlib

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_KEY
db = SQLAlchemy(app)

app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 465,
    MAIL_USE_TLS = False,
    MAIL_USE_SSL = True,
    MAIL_USERNAME = GMAIL_USERNAME,
    MAIL_PASSWORD = GMAIL_PASSWORD,
    MAIL_DEFAULT_SENDER = GMAIL_USERNAME 
))

mail = Mail(app)

###
# Users Table
###

class Users(db.Model):
	
	__tablename__ = 'users'
	
	# Columns	
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String)
	password = db.Column(db.String)
	email = db.Column(db.String)
	forgot_token = db.Column(db.String)
	forgot_timeout = db.Column(db.String)
	facebook_link = db.Column(db.String)
	github_link = db.Column(db.String)
	linkedin_link = db.Column(db.String)
	twitter_link = db.Column(db.String)
	public_profile = db.Column(db.Integer)

	# Backrefs
	projects = relationship("Projects", backref="users", single_parent=True, cascade="all, delete-orphan", primaryjoin=("Users.id==Projects.user_id"))
	project_comments = association_proxy('project_comments','projects')

	# Initialize new user by setting values and adding them right away
	def __init__(self, username, password, email, facebook=None, github=None, linkedin=None, twitter=None):
		self.username = username
		self.password = password
		self.email = email
		self.facebook_link = facebook
		self.github_link = github
		self.linkedin_link = linkedin
		self.twitter_link = twitter
		self.public_profile = 0

	def set_forgot_token(self):
		self.forgot_timeout = time.time() + 86400
		encode_string = self.username + ":" + self.password + ":" + str(time.time())
		self.forgot_token = hashlib.md5(encode_string.encode('utf-8')).hexdigest()		
		db.session.commit()
		
	
	def send_forgot_password_email(self, root):
		self.set_forgot_token()
		msg = Message("Password Reset?", sender=GMAIL_USERNAME, recipients=[self.email])
		msg.html = "Hey " + self.username + ",<br /><br />Visit <a href=\"" + root + "password?token=" + self.forgot_token + "\" target=\"_BLANK\">this link</a> to reset your password. If you have any questions or run into any issues, be sure to reply to this email.<br /><br />Thanks,<br />SDNetworking"
		mail.send(msg)

###
# Projects Table
###
class Projects(db.Model):

	__tablename__ = 'projects'

	# Columns	
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String)
	description = db.Column(db.String)
	user_id = db.Column(db.Integer, ForeignKey('users.id'))
	timestamp = db.Column(db.String)
	
	project_comments = relationship("ProjectComments",backref="projects", single_parent=True, cascade="all, delete-orphan",  primaryjoin=("Projects.id==ProjectComments.project_id"))

	# Set values for Projects
	def __init__(self, title, description):
		updated_title = title.replace("<script","<br />").replace("text/javascript","<br />").replace("</script>","<br />")
		updated_description = description.replace("<script","<br />").replace("text/javascript","<br />").replace("</script>","<br />")
		
		if len(title) == 0 or len(description) == 0 or updated_title != title or updated_description != description:
			self.title = None
			self.description = None
			self.timestamp = None
		else:
			self.title = title
			self.description = description
			self.timestamp = str(time.time())
	
	def get_date(self):
		return (time.strftime('%m/%d',time.localtime(int(float(self.timestamp))))).replace('0','') + (time.strftime('/%Y',time.localtime(int(float(self.timestamp)))))

	def get_time(self):
		return (time.strftime('%I:%M %p', time.localtime(int(float(self.timestamp)))))
	

###
# Project Comments Table
###
class ProjectComments(db.Model):

	__tablename__ = 'project_comments'

	# Columns
	id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer, ForeignKey('projects.id'))
	user_id = db.Column(db.Integer, ForeignKey('users.id'))
	comment = db.Column(db.String)
	timestamp = db.Column(db.String)

	user = relationship("Users", backref="project_comments", single_parent=True, primaryjoin=("Users.id==ProjectComments.user_id"))
	project = relationship("Projects")	

	def __init__(self, comment, user, project):
		updated_comment = comment.replace("<script","<br />").replace("text/javascript","<br />").replace("</script>","<br />")
	
		if len(comment) == 0 or updated_comment != comment:
			self.comment = None
			self.user = None
			self.project = None
			self.timestamp = None
		else:
			self.comment = comment
			self.user = user
			self.project = project
			self.timestamp = str(time.time()) 

	
	def get_date(self):
		return (time.strftime('%m/%d',time.localtime(int(float(self.timestamp))))).replace('0','') + (time.strftime('/%Y',time.localtime(int(float(self.timestamp)))))

	def get_time(self):
		return (time.strftime('%I:%M %p', time.localtime(int(float(self.timestamp)))))

###
# Messages Table
###

class Messages(db.Model):

	___tablename__ = 'messages'

	# Columns
	id = db.Column(db.Integer, primary_key=True)
	from_id = db.Column(db.Integer, ForeignKey('users.id'))
	to_id = db.Column(db.Integer, ForeignKey('users.id'))
	message = db.Column(db.String)
	unread = db.Column(db.Integer)
	timestamp = db.Column(db.String)

	from_user = relationship("Users", primaryjoin=("Users.id==Messages.from_id"))
	to_user = relationship("Users", primaryjoin=("Users.id==Messages.to_id"))

	def __init__(self, from_user, to_user, message):
		self.from_user = from_user
		self.to_user = to_user
		self.message = message
		self.unread = 1
		self.timestamp = str(time.time())



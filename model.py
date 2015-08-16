from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, ForeignKey, String, Column
from sqlalchemy.orm import relationship
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:tPWrd5@localhost/sdn'
db = SQLAlchemy(app)

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
	
	# Backref for Projects table
	projects = relationship("Projects", backref="users")
	
	# Initialize new user by setting values and adding them right away
	def __init__(self, username, password, email):
		self.username = username
		self.password = password
		self.email = email	

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


	# Set values for Projects
	def __init__(self, title, description):
		self.title = title
		self.description = description
		self.timestamp = str(time.time())

	def get_date(self):
		return (time.strftime('%m/%d',time.localtime(int(float(self.timestamp))))).replace('0','') + (time.strftime('/%Y',time.localtime(int(float(self.timestamp)))))

	def get_time(self):
		return (time.strftime('%H:%M %p', time.localtime(int(float(self.timestamp)))))


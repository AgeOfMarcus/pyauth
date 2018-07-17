#!/usr/bin/python3

import sqlite3, hashlib, time
from flask import Flask, jsonify, request
from uuid import uuid4
import _thread

def sql(cmd):
	with sqlite3.connect("users.db") as db:
		cursor = db.cursor()
		res = cursor.execute(cmd).fetchall()
		db.commit()
	return res

authed = {}
maxtime = 60*60*2 #default=2h

queue = {}

def do_queue():
	while True:
		for i in queue:
			res = eval(queue[i]["cmd"])
			queue[i]["res"] = res
			

sql('''CREATE TABLE IF NOT EXISTS users
(ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
USER TEXT NOT NULL,
PASS TEXT NOT NULL);''')

def sha256(string): return hashlib.sha256(string.encode()).hexdigest()

def login(user, passwd):
	cmd = "SELECT ID FROM users WHERE USER='%s' AND PASS='%s'" % (user, passwd)
	res = sql(cmd)
	if not len(res) == 0:
		uuid = str(uuid4())
		authed[user] = {
			'uuid':uuid,
			'time':time.time(),
		}
		return uuid
	return "!login"

def auth(user, uuid):
	if not user in authed:
		return "!nouser"
	if not authed[user]['uuid'] == uuid:
		return "!uuid"
	if (authed[user]['time'] - time.time()) >= maxtime:
		return "!time"
	return "ok"

def logout(user, uuid):
	check = auth(user, uuid)
	if not check == "ok":
		return check
	del authed[user]
	return "ok"

def new_user(user, passwd):
	cmd = '''INSERT INTO users (USER,PASS)
	VALUES ('%s','%s');''' % (user, passwd)
	sql(cmd)
	return "ok"


app = Flask(__name__)

@app.route("/new",methods=['GET'])
def app_new_user():
	user = request.args['user']
	passwd = request.args['pass']
	res = new_user(user,passwd)
	return res, 200

@app.route("/login",methods=['GET'])
def app_login():
	user = request.args['user']
	passwd = request.args['pass']
	res = login(user,passwd)
	return res, 200

@app.route("/auth",methods=['GET'])
def app_auth():
	user = request.args['user']
	token = request.args['token']
	res = auth(user,token)
	return res, 200

@app.route("/logout",methods=['GET'])
def app_logount():
	user = request.args['user']
	token = request.args['token']
	res = logout(user,token)
	return res, 200

@app.route("/",methods=['GET'])
def home_page():
	res = {
		'/new':['user','pass'],
		'/login':['user','pass'],
		'/auth':['user','token'],
	}
	return jsonify(res), 200

if __name__ == "__main__":
	_thread.start_new_thread(do_queue, ( ))
	app.run(host="0.0.0.0",port=5000)

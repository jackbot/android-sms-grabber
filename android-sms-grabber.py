#!/usr/bin/env python
#coding=utf8

# Android SMS grabber
# Jack Weeden 2011 <ajack.org>

import time, sys, subprocess
from os import path

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders

adb = '/usr/local/android/platform-tools/adb'
remote_sms_db = '/data/data/com.android.providers.telephony/databases/mmssms.db'
debug = 0
last_check_file = 'last_check'
email_settings = {
	'username': '',
	'password': '',
	'subject' : 'New SMS'
}
timezone = 1	# I'm GMT+1, messages in the SMS database are timestamped with GMT

def init():

	# Check if adb exists
	if subprocess.call(['which', 'adb']) > 0:
		if debug: print 'adb not found, make sure it\'s in your $PATH'
		exit(1)

	# Check there's a phone connected
	# `adb devices` returns something like
	# List of devices attached 
	# HT111111111  device
	# So we need to check for >1 occurrence of 'device'	
	adb_devices = subprocess.check_output(['adb', 'devices'])
	if adb_devices.count('device') < 2:
		if debug: print 'No phone connected.'
		exit(1)


def last_check_time():

	# When was the last time we checked for SMSs?
	if path.exists(last_check_file):
		with open(last_check_file) as f:
			last_check = f.readline().rstrip()
			if debug: print "Last checked %s" % nice_timestamp(last_check)
			return int(last_check) - (timezone * 3600000)

	return 0
		

def get_new_messages():

	last_check = str(last_check_time())
	if debug: print 'Checking for messages newer than %s' % nice_timestamp(last_check)
	if last_check != 0:
		sql = "SELECT address, date, body FROM sms WHERE date > '%s' ORDER BY date DESC" % str(last_check)
	else:
		sql = "SELECT address, date, body FROM sms ORDER BY date DESC"

	cmd = '%s shell \'sqlite3 %s "%s"\'' % (adb, remote_sms_db, sql)
	process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
	db_dump = process.stdout.read()

	# Some messages are multi-lined so splitting with \n won't be suitable
	messages = []
	ctr = 0

	for line in db_dump.split('\n'):
		parts = line.split('|')
		
		if len(parts) == 3:
			# Got a new message
			messages.append({ 'from': parts[0], 'date' : parts[1], 'message' : parts[2] })
			ctr += 1

		elif line != '' and line != '\n':
			# Line isn't empty so it must belong to the previous message, so append it
			messages[ctr - 1]['message'] += line


	if debug: print messages


	# Send the email - I'm using my own gmail account to send to my own gmail account
	if email_settings['username'] != '' and email_settings['password'] != '' and len(messages) > 0:
		email_messages(messages)


	# Write last check time to the file
	now_ms = int(round(time.time() * 1000)) + (timezone * 3600000)
	with open(last_check_file, 'w') as f:
		f.write(str(now_ms))


	
def email_messages(messages):
	msg = MIMEMultipart()
	msg['From'] = msg['To'] = email_settings['username']
	msg['Subject'] = email_settings['subject']

	# Create the email body
	body = ''
	for sms in messages:
		body += 'From: %s\n'		% sms['from']
		body += 'Time: %s\n'		% nice_timestamp(sms['date'])
		body += 'Message: %s\n\n\n'	% sms['message']

	msg.attach(MIMEText(body))
	server = smtplib.SMTP('smtp.gmail.com')
	server.ehlo()
	server.starttls()
	server.ehlo()
	server.login(email_settings['username'], email_settings['password'])
	server.sendmail(email_settings['username'], email_settings['username'], msg.as_string())
	server.close()


def nice_timestamp(ts_ms):
	# Takes in a timestamp in ms and returns a nice string
	return time.strftime('%a %d %B %H:%M', time.gmtime(int(ts_ms) / 1000))


if __name__ == '__main__':

	if '-d' in sys.argv: debug = 1

	init()

	get_new_messages()


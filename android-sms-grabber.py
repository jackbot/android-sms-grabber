#!/usr/bin/env python
#coding=utf8

# Android SMS grabber
# Jack Weeden 2011 <ajack.org>

import time, sys, subprocess
from os import path

adb = '/usr/local/android/platform-tools/adb'
remote_sms_db = '/data/data/com.android.providers.telephony/databases/mmssms.db'
debug = 1
last_check_file = 'last_check'


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
			if debug: print "Last checked %s" % str(last_check)
			return last_check

	return 0
		

def get_new_messages():

	last_check = last_check_time()
	if last_check != 0:
		sql = "SELECT address, date, body FROM sms WHERE date > '%s'" % last_check
	else:
		sql = "SELECT address, date, body FROM sms"

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

	# Write last check time to the file
	now_ms = int(round(time.time() * 1000))
	with open(last_check_file, 'w') as f:
		f.write(str(now_ms))
	


if __name__ == '__main__':

	if '-q' in sys.argv: debug = 0

	init()

	get_new_messages()


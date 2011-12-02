#Android SMS grabber

Grabs new SMS messages from a phone connected by USB using `adb`.

Useful if you have a phone connected to a machine in a remote place. Just connect the phone via USB, run the Python script in a cron script and do whatever you want with the new messages.


##Method
* The script uses `subprocess` to open `adb` to connect to the phone.
* A command is passed to ADB to execute `sqlite3` on the phone, passing it the SMS database
* A date is read from the `last_check` file in the same directory
* If no file exists, or there is no date in it, the script gets all messages from the phone
* If there is a date, the script checks for messages newer than the contents of the file
* After running, the current timestamp is written to the file, so when we run the script next time, only newer SMSs are returned.


##SMS DB structure
The script currently just pulls __from__, __date__ and __body__ from the SMS db. The full schema for the db is as follows:

	_id INTEGER PRIMARY KEY,
	thread_id INTEGER,
	address TEXT,
	person INTEGER,
	date INTEGER,
	protocol INTEGER,
	read INTEGER DEFAULT 0,
	status INTEGER DEFAULT -1,
	type INTEGER,
	reply_path_present INTEGER,
	subject TEXT,
	body TEXT,
	service_center TEXT,
	locked INTEGER DEFAULT 0


##Notes
I've only tested this on OSX 10.7 with a rooted T-Mobile G1, YMMV.

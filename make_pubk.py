#!/usr/bin/env python

import sys, sqlite3
from sqlite3 import Error

db = "/etc/staticDHCPd/dhcp.sqlite3"

def create_connection(db):
	try:
		conn = sqlite3.connect(db)
		return conn
	except Error as e:
		print(e)
		sys.exit(1)
	return None

def main():
	if len(sys.argv) == 4:
		iid = sys.argv[1]
		user = sys.argv[2]
		key = sys.argv[3]
		key = key.strip()
	elif len(sys.argv) == 5: # read from file, -f given
		p = sys.argv[1]
		if p.strip() == "-f":
			iid = sys.argv[2]
			user = sys.argv[3]
			f = sys.argv[4]
			try:
				with open(f) as file:
					key = file.read()
					key = key.strip()
			except IOError as e:
				print (e.filename + " : "+ e.strerror)
				sys.exit(1)
		else:
			print("Usage: '{prg} instance-id user public_key' or '{prg} -f instance-id user public_key_file'".format(prg = sys.argv[0]))
			sys.exit(1)
	else:
		print("Usage: '{prg} instance-id user public_key' or '{prg} -f instance-id user public_key_file'".format(prg = sys.argv[0]))
		sys.exit(1)

	conn = create_connection(db)
	cur = conn.cursor()

	cur.execute("SELECT * FROM pub_keys WHERE public_key_user = '{u}' AND instance_id = '{i}'".format(u = user, i = iid))
	rows = cur.fetchall()
	if len(rows) > 0: # instance already has that user
		inp = raw_input("This instance already has this user. Do you want to overwrite the public key? [Y/N] ")
		if inp.lower().strip() == "y" or inp.lower().strip() == "yes":
			try:
				cur.execute("UPDATE pub_keys SET public_key = '{k}' WHERE public_key_user = '{u}' AND instance_id = '{i}'".format(k = key, u = user, i = iid))
				conn.commit()
			except Error as e:
				print (e)
				sys.exit(1)
		else:
			print("Aborting")
			sys.exit(0)
	else: # check if instance exists
		cur.execute("SELECT instance_id FROM instance WHERE instance_id = '{i}'".format(i = iid))
		rows = cur.fetchall()
		if len(rows) > 0: #instance exists, go and add user and public key
			try:
				cur.execute("INSERT INTO pub_keys VALUES('{k}', '{u}', '{i}')".format(k = key, u = user, i = iid))
				conn.commit()
			except Error as e:
				print (e)
				sys.exit(1)
		else:
			print("No such instance-id: {i}, aborting".format(i = iid))
			sys.exit(0)
	conn.close()

if __name__ == "__main__":
	main()

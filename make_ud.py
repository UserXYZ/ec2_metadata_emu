#!/usr/bin/env python

from base64 import urlsafe_b64encode
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

def enc_ud(f):
	with open(f) as udf:
		udata = udf.read()
	udf.close()
	
	ud64 = urlsafe_b64encode(udata)
	return ud64

def main():
	if len(sys.argv) == 3:
		f = sys.argv[2]
		iid = sys.argv[1]
	else:
		print("Usage: {prg} instance-id file, where file contains userdata in YAML format").format(prg = sys.argv[0])
		sys.exit(1)

	u64 = enc_ud(f)

	conn = create_connection(db)
	cur = conn.cursor()
	cur.execute("SELECT * FROM userdata WHERE instance_id = '{i}'".format(i = iid))
	rows = cur.fetchall()

	try:
		if len(rows) > 0:
			print("Updating userdata for '{i}'".format(i = iid))
			cur.execute("UPDATE userdata SET udata = '{u}' WHERE instance_id = '{i}'".format (u = u64, i = iid))
		else:
			print("Inserting new userdata for '{i}'".format(i = iid))
			cur.execute("INSERT OR IGNORE INTO userdata (instance_id, udata) VALUES('{i}', '{u}')".format (u = u64, i = iid))
	except Error as e:
		print(e)

	conn.commit()
	conn.close()

if __name__ == "__main__":
	main()

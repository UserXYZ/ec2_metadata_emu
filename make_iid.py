#!/usr/bin/env python

import sys, sqlite3, uuid
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
	if len(sys.argv) == 2:
		mac = sys.argv[1]
	else:
		print("Usage: {prg} mac address, like 'aa:bb:cc:dd:ee:ff'".format(prg = sys.argv[0]))
		sys.exit(1)

	conn = create_connection(db)
	cur = conn.cursor()
	cur.execute("SELECT hostname FROM maps WHERE mac = '{m}'".format(m = mac))
	rows = cur.fetchall()
	for r in rows:
		hostname = str(r[0])
		cur.execute("SELECT mac FROM instance WHERE mac = '{m}'".format(m = mac))
		rows = cur.fetchall()
		if len(rows) > 0:
			print("Instance with mac address {m} is active".format(m = mac))
			sys.exit(1)
		else:
			iid = hostname + "-" + str(uuid.uuid4().get_hex().upper()[0:8])
			try:
				cur.execute("INSERT INTO instance VALUES('{i}', '{m}')".format(i = iid, m = mac))
			except Error as e:
				print (e)
				sys.exit(1)
			conn.commit()
	conn.close()

if __name__ == "__main__":
	main()
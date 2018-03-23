#!/usr/bin/python

import sys, sqlite3
import BaseHTTPServer
from base64 import urlsafe_b64decode
from sqlite3 import Error

#md = {}
db = "/etc/staticDHCPd/dhcp.sqlite3"

MD_TREE = {}
md_ok = False

def create_connection(db):
	try:
		conn = sqlite3.connect(db)
		return conn
	except Error as e:
		print(e)
	return None

def get_iid(conn, mac):
	cur = conn.cursor()
	cur.execute("SELECT instance_id FROM instance WHERE mac = '{m}'".format(m = mac))
	rows = cur.fetchall()
	for row in rows:
		i = str(row[0])
		return i
	return None

def get_pubk(conn, iid):
	keys = []
	pkeys = {}
	
	cur = conn.cursor()
	cur.execute("SELECT * FROM 'pub_keys' WHERE instance_id = '{i}'".format(i = iid))
	rows = cur.fetchall()
	
	for row in rows:
		pubk_user = str(row[1])
		pubk = str(row[0])
		keys.append(pubk)
		pkeys[pubk_user] = keys
	return pkeys

def get_ud(conn, iid, ud):
	cur = conn.cursor()
	cur.execute("SELECT * FROM userdata WHERE instance_id = '{i}'".format(i = iid))
	rows = cur.fetchall()
	for row in rows:
		try:
			ud = urlsafe_b64decode(str(row[1]))
		except TypeError:
			print("Badly encoded user data")
	return ud

def make_md(conn, macaddr, md):
	cur = conn.cursor()
	cur.execute("SELECT * FROM 'maps' WHERE mac = '{m}'".format(m = macaddr))
	rows = cur.fetchall()
	for row in rows:
		hostname = str(row[2]);
		ip = str(row[1]);
		mac = str(macaddr)
		
		iid = get_iid(conn, mac)
		if iid != None:
			md['instance-id'] = iid
		else:
			return None

		md['hostname'] = hostname
		md['local-hostname'] = hostname
		md['local-ipv4'] = ip
		md['mac'] = mac

		network = { 
			'interfaces': {
				'macs': {
					mac: {
						'local-hostname': hostname, 'public-hostname': ip+'-'+hostname+'.localnet',
						'local-ipv4s': ip, 'public-ipv4s': ip, 'mac': mac
						}
					}
				}
			}

		md['network'] = network
		md['public-hostname'] = ip+'-'+hostname+'.localnet'
		md['public-ipv4s'] = ip
		md['public-keys'] = get_pubk(conn, iid)
		
		return md

def fixup_pubkeys(pk_dict, listing):
	i = -1
	mod_cur = {}
	for k in sorted(pk_dict.keys()):
		i = i+1
		if listing:
			mod_cur["%d=%s" % (i, k)] = ""
		else:
			mod_cur["%d" % i] = { "openssh-key": '\n'.join(pk_dict[k]) }
	return(mod_cur)

class myRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

	def get_client_data(self, ip):
		global conn
		global md_ok
		global MD_TREE
		md = {}
		ud = ""
		# get mac address from ip address
		cur = conn.cursor()
		cur.execute("SELECT mac FROM maps WHERE ip = '{i}'".format(i = ip))
		rows = cur.fetchall()
		for r in rows:
			md = make_md(conn, r[0], md) # get metadata
			if md != None:
				md_ok = True
				# get user data
				ud = get_ud(conn, md['instance-id'], ud)
		# nake meta data tree
		MD_TREE = {
					'latest' : { 'user-data' : ud, 'meta-data': md },
					'2009-04-04' : { 'user-data' : ud, 'meta-data': md },
					'2011-01-01' : { 'user-data' : ud, 'meta-data': md },
					'2016-09-02' : { 'user-data' : ud, 'meta-data': md }
					}

	def do_GET(self):
		global md_ok
		global MD_TREE
		
		clientip = self.client_address[0]
		if md_ok == False:
			self.get_client_data(clientip)
		
		toks = [i for i in self.path.split("/") if i != "" ]
		path = '/'.join(toks)

		cur = MD_TREE
		for tok in toks:
			if isinstance(cur, str):
				cur = None
				break
			cur = cur.get(tok, None)
			if cur == None:
				break
			if tok == "public-keys":
				cur = fixup_pubkeys(cur, toks[-1] == "public-keys")

		if cur == None:
			output = None
		elif isinstance(cur,str):
			output = cur
		else:
			mlist = []
			for k in sorted(cur.keys()):
				if isinstance(cur[k], str):
					mlist.append(k)
				else:
					mlist.append("%s/" % k)
					
			output = "\n".join(mlist)

		if cur:
			self.send_response(200)
			self.end_headers()
			self.wfile.write(output)
		else:
			self.send_response(404)
			self.end_headers()
			
		return

	def do_POST(self):
		return

def run_while_true(server_class=BaseHTTPServer.HTTPServer,
                   handler_class=BaseHTTPServer.BaseHTTPRequestHandler,
                   port=80, ipaddr='169.254.169.254'):
	server_address = (ipaddr, int(port))
	httpd = server_class(server_address, handler_class)
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		httpd.server_close()
		conn.close()

#main
args = {}
args['handler_class'] = myRequestHandler
args['port'] = 80
args['ipaddr'] = '169.254.169.254'
# create a database connection
conn = create_connection(db)
#make_md(conn, "52:54:00:5a:b6:61")
#ud = get_ud(conn, md['instance-id'])
#conn.close()
"""
MD_TREE = {
	'latest' : { 'user-data' : ud, 'meta-data': md },
	'2009-04-04' : { 'user-data' : ud, 'meta-data': md },
	'2011-01-01' : { 'user-data' : ud, 'meta-data': md },
	'2016-09-02' : { 'user-data' : ud, 'meta-data': md }
}
"""
if len(sys.argv) == 2:
	toks = sys.argv[1].split(":")
	if len(toks) == 1:
		# port only
		args['port'] = sys.argv[1]
	if len(toks) == 2:
		# host:port
		(args['ipaddr'],args['port']) = toks

print "listening on %s:%s" % (args['ipaddr'], args['port'])
run_while_true(**args)

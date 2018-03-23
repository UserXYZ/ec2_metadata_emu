#!/usr/bin/python
"""
To use this to mimic the EC2 metadata service entirely, run it like:
  # where 'eth0' is *some* interface.  if i used 'lo:0' i got 5 second or so delays on response.
  sudo ifconfig eth0:0 169.254.169.254 netmask 255.255.255.255

  sudo ./mdserv 169.254.169.254:80
Then:
  wget -q http://169.254.169.254/latest/meta-data/instance-id -O -; echo
  curl --silent http://169.254.169.254/latest/meta-data/instance-id ; echo
  ec2metadata --instance-id
"""

import sys
import BaseHTTPServer

# output of: python -c 'import boto.utils; boto.utils.get_instance_metadata()'
md = {
 'hostname': 'cloud1',
 'instance-id': 'a2547ac6',
 'local-hostname': 'cloud1',
 'local-ipv4': '192.168.122.201',
 'mac': '52:54:00:5a:b6:61',
 'network': {
  'interfaces': {
   'macs': {
    '52:54:00:5a:b6:61': {
     'local-hostname': 'cloud1',
     'local-ipv4s': '192.168.122.201',
     'mac': '52:54:00:5a:b6:61',
     'public-hostname': 'cloud1.localnet',
     'public-ipv4s': '192.168.122.201'
    }
   }
  }
 },
 'public-hostname': 'cloud1.localnet',
 'public-ipv4': '192.168.122.201',
 'public-keys': {
  'ubuntu': [
   'ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAo6QxxG8BeZK+AI0QsCDavkx00rt5QveWQ6lXwDG9hkGqmORNvKrrfXobxGGBiTGyzHmfIMVKov0HqpNWgVaNTugIHOfDmFHk6+oPRX0+JpVnrZbLwPUhJobypsaPmc4tvo377rCJHgIQXPgZ1RobZcT4uSuqVECMQtR3AuwvA2Jgjf1waJK0IiKBIzXLS4A1JuR15a3uG2shfPjrq8qDJ7RSfIm+ZFTfQ2sMkmEJ1Ptm4IhwSEDKC7NHJ2mxcjqsJK5+8sZVjwhig7jmbxxm1owZueOHF2SV/R+qdfy20iVyFQa61fMgtkBX1KHWrAwPJTzlqK1J69ybCvU3qaJrpw== root@andrea'
  ]
 }
}

ud = """
#cloud-config
datasource:
  Ec2:
    strict_id: false
packages:
    - ntp
    - mc
    - htop
password: qweqwe123
chpasswd:
  expire: false
ssh_pwauth: True
preserve_hostname: false
timezone: Europe/Belgrade
ntp:
  pools:
    - pool.ntp.org
    - rs.pool.ntp.org
write_files:
  - content: "Done user-data"
    path: /root/done.txt
hostname: cloud1
fqdn: cloud1.localnet
runcmd:
 - [ 'sh', '-c', 'service networking restart' ]
"""

'''
ud = """
I2Nsb3VkLWNvbmZpZwpkYXRhc291cmNlOgogIEVjMjoKICAgIHN0cmljdF9pZDogZmFsc2UKcGFj
a2FnZXM6CiAgICAtIG50cAogICAgLSBtYwojIGNvbmZpZyBzZWN0aW9uCnBhc3N3b3JkOiBxd2Vx
d2UxMjMKY2hwYXNzd2Q6CiAgZXhwaXJlOiBmYWxzZQojICBsaXN0OgojICAgIC0gdWJ1bnR1OnF3
ZXF3ZQojICAgIC0gcm9vdDpxd2Vxd2UxMjMKc3NoX3B3YXV0aDogVHJ1ZQpwcmVzZXJ2ZV9ob3N0
bmFtZTogZmFsc2UKdGltZXpvbmU6IEV1cm9wZS9CZWxncmFkZQpudHA6CiAgcG9vbHM6CiAgICAt
IHBvb2wubnRwLm9yZwogICAgLSBycy5wb29sLm50cC5vcmcKd3JpdGVfZmlsZXM6CiAgLSBjb250
ZW50OiAiRG9uZSB1c2VyLWRhdGEiCiAgICBwYXRoOiAvcm9vdC9kb25lLnR4dApob3N0bmFtZTog
dWNsb2QwMwpmcWRuOiB1Y2xvZDAzLmxvY2FsbmV0Cg==
"""
'''

MD_TREE = {
	'latest' : { 'user-data' : ud, 'meta-data': md },
	'2009-04-04' : { 'user-data' : ud, 'meta-data': md },
	'2011-01-01' : { 'user-data' : ud, 'meta-data': md },
	'2016-09-02' : { 'user-data' : ud, 'meta-data': md }
}

def fixup_pubkeys(pk_dict, listing):
	# if pk_dict is a public-keys dictionary as returned by boto
	# listing is boolean indicating if this is a listing or a item
	#
	# public-keys is messed up. a list of /latest/meta-data/public-keys/
	# shows something like: '0=brickies'
	# but a GET to /latest/meta-data/public-keys/0=brickies will fail
	# you have to know to get '/latest/meta-data/public-keys/0', then
	# from there you get a 'openssh-key', which you can get.
	# this hunk of code just re-works the object for that.
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
	def do_GET(self):

		# set 'path' to "normalized" path, ie without leading
		# or trailing '/' and without double /
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
	"""
	This assumes that keep_running() is a function of no arguments which
	is tested initially and after each request.  If its return value
	is true, the server continues.
	"""
	server_address = (ipaddr, int(port))
	httpd = server_class(server_address, handler_class)
	httpd.serve_forever()

args = { }
args['handler_class'] = myRequestHandler
args['port'] = 80
args['ipaddr'] = '169.254.169.254'
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

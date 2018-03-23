# ec2_metadata_emu
Amazon EC2 metadata server emulator, for use with cloud-init

Based on staticDHCPD and simple Python2 HTTP server, allows for a number of
virtual machines to get all necessary data so they can be automatically
configured by cloud-init mechanism.

All you have to do is create database records for every MAC address which
define VM's IP address, instance-id etc.
The code then generates all necessary meta-data info and puts it
into the database, which is used by staticDHCPD and HTTP server.

Also, user-data can be generated from YAML file, and public keys can be given
for every instance and user on standard input or read from a file.

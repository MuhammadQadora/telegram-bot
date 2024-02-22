# change owner & permission of a key file 
#!/bin/bash
source /run/secrets/my_secret
chmod 400 /$KEY_FILE
chown 999:999 /$KEY_FILE
mongod --replSet $REPLICA_SET --bind_ip_all --keyFile /$KEY_FILE
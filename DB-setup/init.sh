# change owner & permission of a key file 
#!/bin/bash
source /run/secrets/my_secret
sleep 10
chmod 400 /$KEY_FILE
chown 999:999 /$KEY_FILE
mongod --replSet $REPLICA_SET --bind_ip_all --keyFile /$KEY_FILE --fork --logpath /var/log/mongodb/mongod.log
wait

if mongosh ./initiate.js; then
    echo "SUCCESS >>> initiate"
else
    echo "FAILURE >>> initiate"
    exit 1
fi
sleep 30

if mongosh ./createUser.js; then
    echo "SUCCESS >>> createUser"
else
    echo "FAILURE >>> createUser"
    exit 1
fi
sleep 5

if mongosh --host $MONGO_DB1_NAME:$MONGO_PORT -u $ADMIN_USER -p $ADMIN_PASS ./reconfig.js; then
    echo "SUCCESS >>> reConfig"
else
    echo "FAILURE >>> reConfig"
    exit 1
fi
sleep 5
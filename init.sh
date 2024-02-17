#!/bin/bash
sleep 10
chmod 400 /key
chown 999:999 /key
mongod --replSet rs0 --bind_ip_all --keyFile /key --fork --logpath /var/log/mongodb/mongod.log
wait
mongosh --host <<EOF
  var cfg = {
    "_id": "rs0",
    "version": 1,
    "members": [
      {
        "_id": 0,
        "host": "mongo1:27017",
        "priority": 2
      },
      {
        "_id": 1,
        "host": "mongo2:27017",
        "priority": 1
      },
      {
        "_id": 2,
        "host": "mongo3:27017",
        "priority": 0
      },
      {
        "_id": 3,
        "host": "setup:27017",
        "priority": 3
      }
    ]
  };
  rs.initiate(cfg);
EOF

sleep 30
mongosh <<EOF
admin = db.getSiblingDB("admin")
admin.createUser({
user: "${user}",
pwd: "${pass}",
roles: [ { role: "root", db: "admin" } ]
})
EOF
sleep 5
mongosh --host mongo1:27017 -u ${user} -p ${pass} <<EOF
rs.conf()
config = rs.conf()
config.members.pop()
rs.reconfig(config, {force: true})
EOF
sleep 5
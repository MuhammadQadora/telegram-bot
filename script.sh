#!/bin/bash
chmod 400 /key
chown 999:999 /key
mongod --replSet rs0 --bind_ip_all --keyFile /key
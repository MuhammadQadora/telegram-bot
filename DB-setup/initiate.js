try {
    // initiate replSet
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
} catch (error) {
    if (error.message.includes('already')) {
    } else {
        throw new Error('Failed to initiate: ' + error.message);
    }
}
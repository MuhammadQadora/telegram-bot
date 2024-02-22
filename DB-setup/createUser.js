try {
    // create admin user
    db = db.getSiblingDB("admin");
    db.createUser({
        user: "admin",
        pwd: "admin",
        roles: [ { role: "root", db: "admin" } ]
    });
} catch (error) {
    throw new Error('Failed to create user: ' + error.message);
}
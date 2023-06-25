print("Starting mongodb initialization ...");

db = db.getSiblingDB('plc_database')

db.runCommand({ createRole: "readViewCollection",
    privileges: [{ resource: { db: "plc_database", collection: "system.views" }, actions: [ "find"] }],
    roles : []
})
print("Roles creation completed");

db.createUser({
    user: "root",
    pwd: "Marmolada3343$",
    roles:[{role: "userAdmin" , db:"plc_database"}]
})
print("User creation completed");

db.grantRolesToUser('root',['readViewCollection']);
print("Roles assignment completed");

print("End mongodb initialization");
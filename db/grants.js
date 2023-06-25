use('admin')

db.runCommand({ createRole: "readViewCollection",
    privileges: [{ resource: { db: "plc_database", collection: "system.views" }, actions: [ "find"] }],
    roles : []
})

db.createUser({
    user: "root",
    pwd: "Marmolada3343$",
    roles:[{role: "userAdmin" , db:"plc_database"}]
})

db.grantRolesToUser('root',['readViewCollection']);
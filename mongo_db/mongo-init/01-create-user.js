// this file is executed by the official MongoDB image on first startup
db = db.getSiblingDB(process.env.MONGO_APP_DB); // weatherdb
db.createUser({
  user:  process.env.MONGO_APP_USER,           // weatherapp
  pwd:   process.env.MONGO_APP_PASSWORD,       // weatherpass
  roles: [{ role: "readWrite", db: process.env.MONGO_APP_DB }]
});

db.createCollection("observations");
db.observations.createIndex({ city: 1, observed_at_iso: 1 });

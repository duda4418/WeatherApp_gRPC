// Creates the application user, collection, and indexes needed by the service.

const APP_DB = process.env.MONGO_APP_DB || "weatherdb";
const APP_USER = process.env.MONGO_APP_USER || "weatherapp";
const APP_PASS = process.env.MONGO_APP_PASSWORD || "weatherpass";

// Switch to the application database
db = db.getSiblingDB(APP_DB);

// Create application user with readWrite on the app DB
db.createUser({
  user: APP_USER,
  pwd: APP_PASS,
  roles: [{ role: "readWrite", db: APP_DB }]
});


db.createCollection("weather_observations");


db.runCommand({
  collMod: "weather_observations",
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["city", "observation_time", "temp_c"],
      properties: {
        city: { bsonType: "string" },
        provider: { bsonType: "string" },
        observation_time: { bsonType: "date" },
        fetched_at: { bsonType: "date" },
        temp_c: { bsonType: ["double", "int", "decimal"] },
        humidity_pct: { bsonType: ["int", "double", "decimal", "null"] },
        wind_speed_ms: { bsonType: ["double", "int", "decimal", "null"] },
        conditions: { bsonType: ["string", "null"] },
        raw: { bsonType: ["object", "null"] }
      }
    }
  },
  validationLevel: "moderate",
  validationAction: "warn"
});

db.weather_observations.createIndex({ city: 1, observation_time: 1 });

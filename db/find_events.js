/* global use, db */
// MongoDB Playground
// Use Ctrl+Space inside a snippet or a string literal to trigger completions.

// The current database to use.
use('plc_database');

// Search for documents in the current collection.
db.getCollection('Events')
  .find(
    {
        "data.currentPercentage": 100,
        "data.nodetype": "PLCTestbench"
    },
    {
      /*
      * Projection
      * _id: 0, // exclude _id
      * fieldA: 1 // include field
      */
    }
  )
  .sort({
    /*
    * fieldA: 1 // ascending
    * fieldB: -1 // descending
    */
  });
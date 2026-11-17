The program functions, on a structural level, identially to mp2 with the exeption of overal database schema. Mechanically they both employ endpoints to operate an api to recieve, store, and manipulate a database of some description. MP2 stored dataframes against ids, which allowed it to hold multiple tables. With the implementation of sql language, the primay target of the program has gone from a number of table to just one, the movies table. While the pipeline could support more tables with limited modification, it is currently geared to just support the singular table. The API recieves a csv file from the user, it then processes it in the same way mp2 does, confirming it is a valid format. This pipeline then stores the data from that csv into the sql database directly, as aposed to saving and id-tagging an object. Other endpoints then use the sql querying language to interact with and manipulate the lone table stored within the schema. Caching is the major new implementation, rather than just modification of existing structures. Caching works to relieve load from a server by storing queries that are often repeated. This means that instead of spooling the database for each query if there is a large number of idential requests, the server can spool once, log the response, and then distribute to all users with identical requests. The most common real world application of caching for this load bearing purpose is caching a website's landing or home page, so that in times of high trafic the page loads quickly and with lessened load on the surver.


python3 -m uvicorn main:app --reload
http://127.0.0.1:8000/docs


processing sample_data.csv with these requirements

{
  "validation": {
    "required_columns": [
      "title"
    ],
    "numeric_columns": [
      "rating"
    ]
  },
  "processing": {
    "remove_duplicates": true,
    "missing": {
      "enabled": true,
      "axis": "rows"
    },
    "outliers": {
      "enabled": false,
      "columns": [
        "string"
      ],
      "method": "iqr",
      "threshold": 1.5
    }
  }
}


produce this output
{
  "validation_rows_removed": 0,
  "cleaning_report": {
    "rows_before": 20,
    "rows_after": 18,
    "rows_removed": 2,
    "columns_before": 4,
    "columns_after": 4,
    "columns_removed": 0
  }
}

Then, running a search for the titles and year of films with a rating above 8.2 returns this 
[
  {
    "id": 3,
    "title": "Movie C",
    "release_year": "2022"
  },
  {
    "id": 2,
    "title": "Movie B",
    "release_year": "2021"
  },
  {
    "id": 11,
    "title": "Movie K",
    "release_year": "2020"
  },
  {
    "id": 9,
    "title": "Movie I",
    "release_year": "2023"
  },
  {
    "id": 4,
    "title": "Movie D",
    "release_year": "2023"
  },
  {
    "id": 16,
    "title": "Movie P",
    "release_year": "2020"
  }
]

Which you can then limit to the top 3 by rating by repeating the query with a new limit
	
[
  {
    "id": 3,
    "title": "Movie C",
    "release_year": "2022"
  },
  {
    "id": 2,
    "title": "Movie B",
    "release_year": "2021"
  },
  {
    "id": 11,
    "title": "Movie K",
    "release_year": "2020"
  }
]
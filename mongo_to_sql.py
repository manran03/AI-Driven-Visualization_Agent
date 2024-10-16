import sqlite3
import pymongo

# MongoDB connection
mongo_client = pymongo.MongoClient("connection_string")
mongo_db = mongo_client["test_db"]

# SQLite connection
sqlite_conn = sqlite3.connect("attacks.db")
sqlite_cursor = sqlite_conn.cursor()

def migrate_collection(collection_name):
    collection = mongo_db[collection_name]
    documents = list(collection.find())  # Convert cursor to list to iterate multiple times

    # Check if documents are retrieved
    if not documents:
        print(f"No documents found in MongoDB collection: {collection_name}")
        return

    # Dynamically create the SQLite table based on the MongoDB documents
    columns = set()
    for document in documents:
        columns.update(document.keys())
    columns.discard("_id")

    if not columns:
        print(f"No columns found in MongoDB documents for collection: {collection_name}")
        return

    # Generate the CREATE TABLE SQL statement
    create_table_sql = f"CREATE TABLE IF NOT EXISTS {collection_name} (_id TEXT PRIMARY KEY"
    for column in columns:
        create_table_sql += f", {column} TEXT"
    create_table_sql += ")"

    # Create the table
    print(f"Creating table with SQL: {create_table_sql}")
    sqlite_cursor.execute(create_table_sql)

    # Insert MongoDB documents into the SQLite table
    for document in documents:
        columns = list(document.keys())
        values = [str(document.get(col, "")) for col in columns]

        columns_placeholder = ", ".join(columns)
        values_placeholder = ", ".join(["?" for _ in columns])
        insert_sql = f"INSERT INTO {collection_name} ({columns_placeholder}) VALUES ({values_placeholder})"

        print(f"Inserting document with SQL: {insert_sql} and values: {values}")
        try:
            sqlite_cursor.execute(insert_sql, values)
        except sqlite3.OperationalError as e:
            print(f"Failed to insert document: {e}")
            continue

    sqlite_conn.commit()
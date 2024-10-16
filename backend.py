import google.generativeai as genai
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
import os
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
import sqlite3
import re
import base64
import json

record = {
'user_question': None,
'initial_query': None,
'initial_query_error': None,
'recursion_query1': None,
'recursion_query_error1': None,
'recursion_query2': None,
'recursion_query_error2': None,
'recursion_query3': None,
'recursion_query_error3': None,
'initial_code': None,
'initial_code_error': None,
'recursion_code1': None,
'recursion_code_error1': None,
'recursion_code2': None,
'recursion_code_error2': None,
'recursion_code3': None,
'recursion_code_error3': None,
'executed': False
}

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure Google Generative AI
genai.configure(api_key=GOOGLE_API_KEY)
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

# Initialize the database
db = SQLDatabase.from_uri("sqlite:///converted_database.db")

def check_sql_query(query: str) -> int:
    # Define a list of DML and other potentially destructive SQL statements
    destructive_statements = ["DELETE", "UPDATE", "DROP", "INSERT", "ALTER", "TRUNCATE"]

    # Convert the query to uppercase to make the check case-insensitive
    query_upper = query.upper()

    # Check if any of the destructive statements are in the query
    for statement in destructive_statements:
        if re.search(r'\b' + statement + r'\b', query_upper):
            return -1

    # If none of the destructive statements are found, return 1
    return 1

def record_history():

    try:
        # Establish a database connection
        conn = sqlite3.connect('memory.db')
        cursor = conn.cursor()

        # SQL insert statement
        insert_sql = """
        INSERT INTO records (
            user_question, initial_query, initial_query_error0, recursion_query1,
            recursion_query_error1, recursion_query2, recursion_query_error2,
            recursion_query3, recursion_query_error3, initial_code0,
            initial_code_error0, recursion_code1, recursion_code_error1,
            recursion_code2, recursion_code_error2, recursion_code3,
            recursion_code_error3, executed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        # Prepare the record data
        record_data = (
            record.get('user_question', None),
            record.get('initial_query', None),
            record.get('initial_query_error', None),
            record.get('recursion_query1', None),
            record.get('recursion_query_error1', None),
            record.get('recursion_query2', None),
            record.get('recursion_query_error2', None),
            record.get('recursion_query3', None),
            record.get('recursion_query_error3', None),
            record.get('initial_code', None),
            record.get('initial_code_error', None),
            record.get('recursion_code1', None),
            record.get('recursion_code_error1', None),
            record.get('recursion_code2', None),
            record.get('recursion_code_error2', None),
            record.get('recursion_code3', None),
            record.get('recursion_code_error3', None),
            record.get('executed', False)
        )

        # Execute the insert statement
        cursor.execute(insert_sql, record_data)
        conn.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()


    return 0

def replace_keywords(text):
    keywords = ["```", "sql", "python","json"]
    for keyword in keywords:
        text = text.replace(keyword, "")
    return text

# Get the schema from the database
schema = db.table_info

def end_session():
    try:
        # Connect to SQLite database
        conn = sqlite3.connect('memory.db')
        cursor = conn.cursor()

        # Delete all records from responses table
        cursor.execute('DELETE FROM responses')
        conn.commit()

        # Verify if the table is empty
        cursor.execute('SELECT COUNT(*) FROM responses')
        count = cursor.fetchone()[0]
        conn.close()

        if count == 0:
            print("Table is empty.")
        else:
            print(f"Table is not empty. {count} records remain.")
    except Exception as e:
        print(f"Error during end session: {e}")
    return 0

def update_memory(user_question, llm_response):
    # Connect to SQLite database
    conn = sqlite3.connect('memory.db')

    # Create a cursor object to interact with the database
    cursor = conn.cursor()

    # Insert data into the responses table
    cursor.execute('''
    INSERT INTO responses (user_question, llm_response)
    VALUES (?, ?)
    ''', (user_question, llm_response))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

def create_query(llm, schema, question):
    prompt = """
    You are a SQL expert. Given below is the SQL table schema and a user question.
    Your task is to intelligently create a SQL query that accurately fetches the data required by the user.
    also classify the query based on the user question if the question can be answered in simple text (type=text), if user wants a csv (type=csv) and if plot then (type=plot)
    output in json pls

    you can only use the columns given below cannot write query using any other columns

    Schema:
    {schema}

    User question:
    {question}

    Please ensure the query adheres to the following:
    - Select relevant columns based on the user's question.
    - Use appropriate SQL functions for aggregations, filtering, and grouping.
    - Use JSON functions for nested fields, if necessary.
    - Ensure the query is syntactically correct.

    Examples:

    Example 1:
    Input: Pie chart for count of attacks by attack type
    Output:
      "type": "plot",
      "query": "SELECT attack_type, COUNT(*) FROM attack_data GROUP BY attack_type;"


    Example 2:
    Input: Bar chart showing number of attacks per day
    Output:
      "type": "plot",
      "query": "SELECT DATE(timestamp) as day, COUNT(*) FROM attack_data GROUP BY day;"


    Example 3:
    Input: Total count of attacks for each country
    Output:
      "type": "text",
      "query": "SELECT geoip ->> 'country' AS country, COUNT(*) FROM attack_data GROUP BY country;"


    Example 4:
    Input: List all distinct sensor IPs used in attacks
    Output:
      "type": "csv",
      "query": "SELECT DISTINCT sensor_ip FROM attack_data;"


    Example 5:
    Input: Get attack count and sum of counts for each attack type
    Output:
      "type": "text",
      "query": "SELECT attack_type, COUNT(*) AS attack_count, SUM(count) AS total_count FROM attack_data GROUP BY attack_type;"


    Example 6:
    Input: Average number of attacks per day for DNS
    Output:
    "type": "text",
    "query": "SELECT DATE(timestamp) as day, AVG(count) AS average_attacks FROM attack_data WHERE attack_type = 'DNS' GROUP BY day;"


    Example 7:
    Input: Count of attacks per victim IP range
    Output:
      "type": "csv",
      "query": "SELECT victim_ip_range, COUNT(*) FROM attack_data GROUP BY victim_ip_range;"


    Example 8:
    Input: Count of attacks per day, filtered by a specific attack type 'SSDP'
    Output:
      "type": "plot",
      "query": "SELECT DATE(timestamp) as day, COUNT(*) FROM attack_data WHERE attack_type = 'SSDP' GROUP BY day;"


    Example 9:
    Input: Export attack details to CSV
    Output:
      "type": "csv",
      "query": "SELECT * FROM attack_data;"

    Example 10:
    Input: name the country with most numbe rof attacks
    Output:
        "type":"text"
        "query":"SELECT geoip ->> 'country' AS country, COUNT(*) AS attack_count FROM attack_data GROUP BY country ORDER BY attack_count DESC LIMIT 1"

    Please return only the SQL query and the type in the specified format and and nothing else.
"""

    template = PromptTemplate(input_variables=["schema", "question"], template=prompt)
    chain = template | llm | StrOutputParser()
    record["user_question"]=question
    airesponse=replace_keywords(chain.invoke({"question": question, "schema": schema}))
    response_json = json.loads(airesponse)
    update_memory(prompt.format(schema=schema,question=question), airesponse)
    return response_json

def if_query_error(question, query, schema, depth=0, max_depth=3):
    if depth > max_depth:
        record_history()
        raise ValueError("Recursion limit reached for query correction.")
    try:
        result = db.run(query)
        if depth==0:
            record["initial_query"]=query
        else:
            record["recursion_query"+str(depth)]=query
        return result
    except Exception as e:
        if depth==0:
            record["initial_query_error"]=e
        else:
            record["recursion_query_error"+str(depth)]=e
        prompt = """
        Given below is a user question, schema, query, and the error.

        Question: {question}
        Schema: {schema}
        Query: {query}
        Error: {e}

        Correct the query and return only the corrected query without any extra text.
        """
        template = PromptTemplate(input_variables=["question", "schema", "query", "e"], template=prompt)
        chain = template | llm | StrOutputParser()
        corrected_query = replace_keywords(chain.invoke({"question": question, "schema": schema, "query": query, "e": str(e)}))
        update_memory(prompt.format(question=question, schema=schema, query=query, e=str(e)), corrected_query)
        return if_query_error(question, corrected_query, schema, depth + 1, max_depth)


def create_code(llm, schema, question, query):
    prompt = """
    Write a Python script that processes data fetched by a SQL query and generates output based on user requirements.
    The data from the query is stored in the global variable `query_data`.

    Inputs:
    - `query`: The SQL query used to fetch data.
    - `user_question`: The user's question specifying the desired output.
    - `type`: The format of the output (`text`, `csv`, or `plot`).
    - `schema`: The database schema.

    Requirements:
    - For `type='text'`: Generate a Python script to store the query_data in a text file named `finalrespo.txt`.
    - For `type='csv'`: Generate a Python script to store the query_data in a CSV file named `finalrespo.csv` using the `csv` module.
    - For `type='plot'`: Generate a graph using `matplotlib` and save it as `finalrespo.png`.

    Ensure the script includes necessary imports and setup for `matplotlib`, ensuring the graph displays inline if running in a Jupyter notebook or renders in a web browser otherwise.

    Example:
    - User question: 'Create a pie chart for count of attacks by attack type.'
    - SQL query: `SELECT attack_type, COUNT(*) FROM attack_data GROUP BY attack_type ORDER BY attack_count DESC`
    - Type: `plot`

    The output code should:
    1. Import necessary libraries.
    2. Convert `query_data` to a list of tuples.
    3. Unpack data into separate lists.
    4. Handle errors in data conversion and unpacking.
    5. Generate the required output based on the specified type.

    Example conversion:

    import ast

    global query_data
    # Convert the string to a list of tuples
    try:
        query_data = ast.literal_eval(query_data)
    except (ValueError, SyntaxError) as e:
        print("Error converting query_data string:", e)
        query_data = []


        Sample codes:

    Text Output
    import ast

    global query_data
    # Convert the string to a list of tuples
    try:
        query_data = ast.literal_eval(query_data)
    except (ValueError, SyntaxError) as e:
        print("Error converting query_data string:", e)
        query_data = []

    # Write data to text file
    with open('finalrespo.txt', 'w') as f:
        for item in query_data:
            f.write(f"item[0]: item[1]\n")

    CSV Output

    import ast
    import csv

    global query_data
    # Convert the string to a list of tuples
    try:
        query_data = ast.literal_eval(query_data)
    except (ValueError, SyntaxError) as e:
        print("Error converting query_data string:", e)
        query_data = []

    # Write data to CSV file
    with open('finalrespo.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['attack_type', 'attack_count'])
        writer.writerows(query_data)

    Plot Output
    import ast
    import matplotlib.pyplot as plt

    global query_data
    # Convert the string to a list of tuples
    try:
        query_data = ast.literal_eval(query_data)
    except (ValueError, SyntaxError) as e:
        print("Error converting query_data string:", e)
        query_data = []

    # Unpack the data into separate lists
    try:
        attack_types, attack_counts = zip(*query_data)
    except ValueError as e:
        print("Error unpacking data:", e)
        attack_types, attack_counts = [], []

    # Create pie chart
    plt.figure(figsize=(10, 6))
    plt.pie(attack_counts, labels=attack_types, autopct='%1.1f%%')
    plt.title('Count of Attacks by Attack Type')
    plt.savefig('finalrespo.png')

    
    Only return the Python script for the specified output format.

more examples:
    query: SELECT geoip ->> 'country' AS country, COUNT(*) AS attack_count FROM attack_data GROUP BY country ORDER BY attack_count DESC LIMIT 1
    type:text
    code:
import ast
global query_data
    # Convert the string to a list of tuples
try:
    query_data = ast.literal_eval(query_data)
except (ValueError, SyntaxError) as e:
    print("Error converting query_data string:", e)
    query_data = []

# Write data to text file
with open('finalrespo.txt', 'w') as f:
    for item in query_data:
        f.write(f"item[0]: item[1]\n")


    Query: {query}
    User question: {question}
    Type: {type}
    Schema: {schema}
    """

    template = PromptTemplate(input_variables=["schema", "question", "query","type"], template=prompt)
    chain = template | llm | StrOutputParser()
    airesponse = replace_keywords(chain.invoke({"schema": schema, "question": question, "query": query,"type":query["type"]}))
    update_memory(prompt.format(schema=schema, question=question, query=query["query"], type=query["type"]), airesponse)
    return airesponse

def if_code_error(llm, schema, question, query, code, exec_globals, depth=0, max_depth=3):
    if depth > max_depth:
        record_history()
        raise ValueError("Recursion limit reached for code correction.")
    try:
        exec(code, exec_globals)
        if depth==0:
            record["initial_code"]=code
        else:
            record["recursion_code"+str(depth)]=code
        record["executed"]=True
    except Exception as e:
        if depth==0:
            record["initial_code_error"]=e
        else:
            record["recursion_code_error"+str(depth)]=e
        prompt = """
        Given below is a user question, schema, SQL query, generated Python code, and the error encountered when executing the code.

        Question: {question}
        Schema: {schema}
        Query: {query}
        Code: {code}
        Error: {e}

        Correct the Python code and return only the corrected code without any extra text.
        """
        template = PromptTemplate(input_variables=["question", "schema", "query" "code", "e"], template=prompt)
        chain = template | llm | StrOutputParser()
        corrected_code = replace_keywords(chain.invoke({"question": question, "schema": schema, "query": query, "code": code, "e": str(e)}))
        update_memory(prompt.format(question=question, schema=schema, query=query, code=code, e=str(e)), corrected_code)
        return if_code_error(llm, schema, question, query, corrected_code, exec_globals, depth + 1, max_depth)

def file_to_base64(file_path):
    try:
        # Read the file in binary mode
        with open(file_path, 'rb') as file:
            file_content = file.read()
        
        # Encode the binary content to base64
        base64_encoded = base64.b64encode(file_content)
        
        # Convert the base64 bytes to a string and return
        return base64_encoded.decode('utf-8')
    except Exception as e:
        return f"An error occurred: {e}"

def main(question):
    query = create_query(llm, schema, question)
    print("query:::",query["query"])
    print("type:::",query["type"])
    if check_sql_query(query["query"])==-1:
        return "Please Try Again"
    result = if_query_error(question, query["query"], schema)
    print("data:::",result)
    python_code = create_code(llm, schema, question, query)
    print("code:::",python_code)
    exec_globals = {'query_data': result}
    corrected_code = if_code_error(llm, schema, question, query["query"], python_code, exec_globals)
    record_history()

    if query["type"] =="text":
        retstr=file_to_base64("finalrespo.txt")
    elif query["type"] =="plot":
        retstr=file_to_base64("finalrespo.png")
    if query["type"] =="csv":
        retstr=file_to_base64("finalrespo.csv")
    return {"type":query["type"],'file': retstr}

    


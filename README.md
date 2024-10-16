# NLP SQL Querying App

This repository contains a web application that allows users to ask natural language questions, which are converted into SQL queries and executed against a database. The app generates SQL queries, corrects them in case of errors, and processes the data with Python scripts. It supports returning results in text, CSV, or plot formats, and allows saving results as files. Additionally, the project includes functionality for generating fake data with Faker, populating a MongoDB database, and converting it into a SQLite database.

## Table of Contents
1. [Project Structure](#project-structure)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
5. [API Endpoints](#api-endpoints)
6. [File Upload Formats](#file-upload-formats)
7. [Fake Data Generation](#fake-data-generation)
8. [Demo](#Demo)

## Project Structure

📦nlp-sql-querying-app ┣ 📂backend ┃ ┣ 📜app.py # Main Flask app for handling NLP queries ┃ ┣ 📜main.py # Main function to process queries and generate responses ┃ ┣ 📜data_gen.py # Python script to generate fake data using Faker ┃ ┣ 📜db_converter.py # Script to convert MongoDB data to SQLite database ┃ ┣ 📜requirements.txt # Dependencies for the project ┣ 📜README.md # Readme file

## Features
- Natural language SQL querying using Google Generative AI (Gemini Model).
- Query correction and recursion up to 3 attempts.
- Generates responses as text, CSV, or plots (saved as files).
- Generates fake data using `Faker` and populates MongoDB.
- Converts MongoDB database to SQLite database for querying.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/your_username/nlp-sql-querying-app.git
    cd nlp-sql-querying-app
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Set up environment variables in a `.env` file:
    ```env
    GOOGLE_API_KEY=your_google_api_key
    ```

4. Run the Flask app:
    ```bash
    python backend/app.py
    ```

## Usage

To use the NLP SQL querying app:

1. Start the app by running:
    ```bash
    python backend/app.py
    ```

2. Send a POST request to `http://localhost:5002/nlpquery` with a JSON payload:
    ```json
    {
        "question": "Your natural language question"
    }
    ```

3. The response will contain the result type and base64-encoded content, which can be decoded into the respective file.

## API Endpoints

- `/nlpquery`: Takes a natural language question and returns the result as text, CSV, or plot.

## File Upload Formats

- `text`: Returns the result in a `.txt` file.
- `csv`: Returns the result in a `.csv` file.
- `plot`: Returns a plot in `.png` format.

## Fake Data Generation

The project includes a script for generating fake data using `Faker` and populating a MongoDB database.

1. Run the `data_gen.py` file to generate fake data:
    ```bash
    python backend/data_gen.py
    ```

2. Run the `db_converter.py` file to convert MongoDB data into a SQLite database:
    ```bash
    python backend/db_converter.py
    ```
## Demo


**Author**: Your Name
**License**: MIT


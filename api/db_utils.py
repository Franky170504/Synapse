import os
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

# Load environment variables from .env file
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "cursorclass": DictCursor
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

# ---------------------------
# Application Logs
# ---------------------------
def create_application_logs():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS application_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    user_query TEXT,
                    response TEXT,
                    model VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()
    finally:
        conn.close()

def insert_application_logs(session_id, user_query, response, model):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO application_logs (session_id, user_query, response, model)
                VALUES (%s, %s, %s, %s)
            """, (session_id, user_query, response, model))
        conn.commit()
    finally:
        conn.close()


def get_chat_history(session_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT user_query, response
                FROM application_logs
                WHERE session_id = %s
                ORDER BY created_at ASC
            """, (session_id,))
            rows = cursor.fetchall()
        
        # Convert the database rows into a list of message objects
        chat_history_messages = []
        if rows:
            for row in rows:
                chat_history_messages.append(HumanMessage(content=row['user_query']))
                chat_history_messages.append(AIMessage(content=row['response']))
        
        return chat_history_messages
    finally:
        conn.close()

# ---------------------------
# Document Store
# ---------------------------
def create_document_store():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()
    finally:
        conn.close()

def insert_document_record(filename):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO documents (filename)
                VALUES (%s)
            """, (filename,))
            conn.commit()
            return cursor.lastrowid  # return file_id
    finally:
        conn.close()

def delete_document_record(file_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM documents WHERE id = %s", (file_id,))
        conn.commit()
        return True
    finally:
        conn.close()

def get_all_documents():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Use 'AS' to rename the column in the query result
            sql_query = """
                SELECT id, filename, uploaded_at AS upload_timestamp
                FROM documents 
                ORDER BY uploaded_at DESC
            """
            cursor.execute(sql_query)
            documents = cursor.fetchall()
        return documents
    finally:
        conn.close()

# ---------------------------
# Initialize tables
# ---------------------------
create_application_logs()
create_document_store()

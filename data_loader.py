import os
import pandas as pd
import sqlite3
from pathlib import Path
from config import DATABASE_URL

class DataLoader:
    def __init__(self, db_path=DATABASE_URL):
        """Initialize the DataLoader with a database path."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect_db(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def close_db(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def load_csv_files(self, data_dir='data'):
        """
        Load all CSV files from the specified directory into SQLite database.
        Creates tables dynamically based on CSV file names and their structure.
        """
        try:
            self.connect_db()
            
            csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
            
            for csv_file in csv_files:
                file_path = os.path.join(data_dir, csv_file)
                df = pd.read_csv(file_path)
                
                table_name = os.path.splitext(csv_file)[0].replace(' ', '_').lower()
                
                self.store_metadata(table_name, list(df.columns))
                
                df.to_sql(table_name, self.conn, if_exists='replace', index=False)
                
                print(f"Loaded {csv_file} into table {table_name}")
                
            self.conn.commit()
            
        except Exception as e:
            print(f"Error loading CSV files: {str(e)}")
            raise
        finally:
            self.close_db()

    def store_metadata(self, table_name, columns):
        """Store table metadata including column names."""

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS table_metadata (
                table_name TEXT,
                column_name TEXT,
                PRIMARY KEY (table_name, column_name)
            )
        ''')
        
        for column in columns:
            self.cursor.execute('''
                INSERT OR REPLACE INTO table_metadata (table_name, column_name)
                VALUES (?, ?)
            ''', (table_name, column))

    def get_table_info(self):
        """Retrieve information about all tables and their columns."""
        try:
            self.connect_db()
            self.cursor.execute('SELECT table_name, GROUP_CONCAT(column_name) as columns FROM table_metadata GROUP BY table_name')
            return self.cursor.fetchall()
        finally:
            self.close_db()

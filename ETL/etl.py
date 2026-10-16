import os
import glob
import pyarrow.parquet as pq    
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values

# Database connection configuration 
# (You can use environment variables or update these with your Render/local connection details)
DB_HOST = os.getenv("DB_HOST", "dpg-db8meom89jmc73engu4g-a.virginia-postgres.render.com")
DB_NAME = os.getenv("DB_NAME", "dbdatabase_3hjb")
DB_USER = os.getenv("DB_USER", "ijrl")
DB_PASSWORD = os.getenv("DB_PASSWORD", "L8mlxHS47VHV1sJWavdDgiRFYByekdWe")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )

def load_parquet_files(data_dir="data"):
    # Find all parquet files in the specified directory
   # search_path = os.path.join(data_dir, "*.parquet")
    parquet_files = ['data/vehicle_status.parquet', 'data/vehicle_kind.parquet' , 'data/fuel_type.parquet', 'data/vehicle_type.parquet', 'data/parking_area.parquet', 'data/vehicle.parquet', 'data/driver.parquet', 'data/road_segment.parquet', 'data/location_ping.parquet', 'data/vehicle_assignment.parquet', 'data/trip.parquet']


    
    if not parquet_files:
        print(f"No Parquet files found in directory: {data_dir}")
        return

    conn = get_connection()
    cursor = conn.cursor()

    for file_path in parquet_files:
        # Extract table name from filename (e.g., 'data/driver.parquet' -> 'driver')
        base_name = os.path.basename(file_path)
        table_name = os.path.splitext(base_name)[0]
        
        print(f"Processing table '{table_name}' from {file_path}...")
        
        try:
            
            df = pq.read_table(file_path)

            # Prepare columns and tuple values for bulk insertion
            columns = df.column_names
            values = [
                tuple(row[column] for column in columns)
                for row in df.to_pylist()
            ]

            if not values:
                print(f"Table '{table_name}' file is empty. Skipping.")
                continue

            query = sql.SQL(
                "INSERT INTO {} ({}) VALUES %s ON CONFLICT DO NOTHING"
            ).format(
                sql.Identifier(table_name),
                sql.SQL(", ").join(sql.Identifier(column) for column in columns),
            )

            # Execute bulk insertion
            execute_values(cursor, query, values)
            conn.commit()
            print(f"Successfully loaded {len(values)} rows into table '{table_name}'.")

        except Exception as e:
            conn.rollback()
            print(f"Error loading table '{table_name}': {e}")

    cursor.close()
    conn.close()
    print("ETL pipeline execution completed.")

if __name__ == "__main__":
    # Specify the folder where your 11 Parquet files are stored
    data_directory = os.getenv("DATA_DIR", "data")
    load_parquet_files(data_directory)
import json
import psycopg2
import os
import argparse
import sys

def upload(file):
    # Connect to your PostgreSQL database
    conn = psycopg2.connect("host=localhost port=5432 dbname=postgres user=postgres password=postgres")
    cur = conn.cursor()

    try:
        # Read the JSONL file
        with open(file, 'r') as f:
            for line in f:
                data = json.loads(line)
                
                # Extract file information from path
                path = data.get('path', '')
                file_name = os.path.basename(path)
                file_extension = os.path.splitext(file_name)[1].lstrip('.') if '.' in file_name else ''
                
                # Get file size (if available in data, otherwise default to 0)
                file_size = data.get('file_size', 0)
                
                # Get other fields (with defaults if not present)
                method_signature = data.get('method_signature', '')
                chunk_type = data.get('chunk_type', 'file')  # Default to 'file' if not specified
                method_index = data.get('method_index', 0)
                content = data.get('content', '')
                
                # Insert into the updated table structure
                cur.execute(
                    """INSERT INTO codebase 
                       (path, file_name, file_extension, file_size, method_signature, 
                        chunk_type, method_index, content) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (path, file_name, file_extension, file_size, method_signature, 
                     chunk_type, method_index, content)
                )

        conn.commit()
        print(f"Successfully uploaded data from {file}")
        return 0
    except Exception as e:
        print(f"Error uploading data: {e}")
        return 1
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Upload JSONL data to PostgreSQL database')
    parser.add_argument('file', nargs='?', default="docs.jsonl", 
                        help='Path to the JSONL file to upload (default: docs.jsonl)')
    
    args = parser.parse_args()
    
    sys.exit(upload(args.file))
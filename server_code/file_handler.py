import anvil.email
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import pandas as pd
import io
from datetime import datetime
import time

@anvil.server.callable
def flight_size():
    return len(app_tables.flights.search())

@anvil.server.callable
def receive_file(file, rows_completed=0):
    """
    Processes Excel (.xls, .xlsx) or CSV files and loads entries into flights table.
    Handles missing headers by creating default column names.
    Only adds entries that don't already exist (checks all values for exact match).
    Works in chunks to avoid timeout - returns after 20 seconds to allow continuation.
    
    Args:
        file: Anvil Media object containing the uploaded file
        rows_completed: Number of rows already processed (for continuation)
        
    Returns:
        dict: {'complete': bool, 'total_rows': int, 'rows_processed': int}
    """
    start_time = time.time()
    timeout_limit = 20  # seconds
    
    # Get file content as bytes
    file_bytes = file.get_bytes()
    file_name = file.name.lower() if hasattr(file, 'name') else ''
    
    # Detect file type and read accordingly
    df = None
    
    if file_name.endswith('.csv'):
        # Try reading CSV with different encodings
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding='latin-1')
            except Exception:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding='iso-8859-1')
                
    elif file_name.endswith('.xlsx'):
        df = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl')
        
    elif file_name.endswith('.xls'):
        df = pd.read_excel(io.BytesIO(file_bytes), engine='xlrd')
        
    else:
        # Try to auto-detect file type
        try:
            # Try Excel first (most common)
            df = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl')
        except Exception:
            try:
                df = pd.read_excel(io.BytesIO(file_bytes), engine='xlrd')
            except Exception:
                # Fall back to CSV
                df = pd.read_csv(io.BytesIO(file_bytes), encoding='utf-8')
    
    # Check if the first row looks like data instead of headers
    if df is not None and len(df) > 0:
        # If all column names are generic (Unnamed) or numeric, assume no headers
        unnamed_cols = sum(1 for col in df.columns if str(col).startswith('Unnamed') or isinstance(col, int))
        
        if unnamed_cols == len(df.columns):
            # No headers detected - read again without header row
            if file_name.endswith('.csv'):
                try:
                    df = pd.read_csv(io.BytesIO(file_bytes), encoding='utf-8', header=None)
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(io.BytesIO(file_bytes), encoding='latin-1', header=None)
                    except Exception:
                        df = pd.read_csv(io.BytesIO(file_bytes), encoding='iso-8859-1', header=None)
            else:
                engine = 'openpyxl' if file_name.endswith('.xlsx') else 'xlrd'
                df = pd.read_excel(io.BytesIO(file_bytes), engine=engine, header=None)
            
            # Create default column names: Column_1, Column_2, etc.
            df.columns = [f'Column_{i+1}' for i in range(len(df.columns))]
        else:
            # Clean up column names - replace NaN or empty strings
            new_columns = []
            for i, col in enumerate(df.columns):
                if pd.isna(col) or str(col).strip() == '':
                    new_columns.append(f'Column_{i+1}')
                else:
                    new_columns.append(str(col).strip())
            df.columns = new_columns
    
    # Ensure the DataFrame is valid before converting to a list of dictionaries
    if df is None or df.empty:
        return {'total_rows': 0, 'added_rows': 0}


    # Replace NaN values with None for better JSON serialization
    df = df.where(pd.notnull(df), None)

    # Ensure all column names are strings
    df.columns = [str(col) for col in df.columns]

    # Convert all columns to strings to ensure consistency
    df = df.astype(str)

    # Convert to list of dictionaries
    try:
        data_list = df.to_dict('records')
        print(data_list[0:5])
    except Exception as e:
        raise Exception(f"Error converting DataFrame to list of dictionaries: {str(e)}")
    
    # Process each entry to ensure proper data types and remove NaN values
    for entry in data_list:
        # First pass: Check for and replace any remaining NaN values
        for key in list(entry.keys()):
            val = entry[key]
            # Check if value is NaN (works for both float NaN and pandas NaT)
            if val is not None and ((isinstance(val, float) and pd.isna(val)) or pd.isna(val)):
                entry[key] = None
        
        # Convert FltDate to date object
        if 'FltDate' in entry and entry['FltDate'] is not None:
            try:
                # Handle various date formats
                date_value = entry['FltDate']
                if isinstance(date_value, str):
                    # Try parsing common date formats
                    for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d']:
                        try:
                            entry['FltDate'] = datetime.strptime(date_value, fmt).date()
                            break
                        except ValueError:
                            continue
                    else:
                        # If no format matched, try pandas parser
                        entry['FltDate'] = pd.to_datetime(date_value).date()
                elif isinstance(date_value, datetime):
                    entry['FltDate'] = date_value.date()
                elif hasattr(date_value, 'date'):
                    entry['FltDate'] = date_value.date()
            except Exception:
                # If conversion fails, set to None
                entry['FltDate'] = None
        
        # Convert Air Time to float or 0.0 if None/NaN
        if 'Air Time' in entry:
            try:
                val = entry['Air Time']
                if val is None or (isinstance(val, str) and val.strip().lower() in ['', 'nan', 'none']):
                    entry['Air Time'] = 0.0
                elif isinstance(val, float) and pd.isna(val):
                    entry['Air Time'] = 0.0
                else:
                    entry['Air Time'] = float(val)
            except (ValueError, TypeError):
                entry['Air Time'] = 0.0
        
        # Convert Block Time to float or 0.0 if None/NaN
        if 'Block Time' in entry:
            try:
                val = entry['Block Time']
                if val is None or (isinstance(val, str) and val.strip().lower() in ['', 'nan', 'none']):
                    entry['Block Time'] = 0.0
                elif isinstance(val, float) and pd.isna(val):
                    entry['Block Time'] = 0.0
                else:
                    entry['Block Time'] = float(val)
            except (ValueError, TypeError):
                entry['Block Time'] = 0.0
        
        # Convert all other fields to strings (except None values)
        for key, value in entry.items():
            if key not in ['FltDate', 'Air Time', 'Block Time']:
                if value is not None:
                    entry[key] = str(value)
    
    # Load the entire flights table into a list of dictionaries (db_1)
    db_1 = [dict(row) for row in app_tables.flights.search()]
    # db_1 = [row.to_dict() for row in app_tables.flights.search()]

    # Remove entries in db_2 that already exist in db_1
    db_2 = data_list
    db_2 = [
        entry for entry in db_2
        if entry not in db_1
    ]

    total_rows = len(db_2)
    rows_processed = rows_completed

    # Add remaining entries in db_2 to the flights table
    for i in range(rows_completed, total_rows):
        # Check timeout - return early if approaching limit
        if time.time() - start_time > timeout_limit:
            return {
                'complete': False,
                'total_rows': total_rows,
                'rows_processed': rows_processed
            }

        entry = db_2[i]
        app_tables.flights.add_row(**entry)
        rows_processed += 1

    # All rows completed
    return {
        'complete': True,
        'total_rows': total_rows,
        'rows_processed': rows_processed
    }

@anvil.email.handle_message
def handle_incoming_emails(msg):

  for a in msg.attachments:
    pass
import anvil.email
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil.tables import query as q
import anvil.server
import pandas as pd
import io
from datetime import datetime, timedelta
import time
import anvil.http

# Define constants for column names
TAKEOFF_TIME_COLUMN = 'Takeoff Time'
FLT_DATE_COLUMN = 'FltDate'
AIR_TIME_COLUMN = 'CFL_Air_Time'
BLOCK_TIME_COLUMN = 'CFL_Block_Time'
REGO_COLUMN = 'Rego'
AC_TYPE_COLUMN = 'ACType'
AD_HOC_CLIENT_NAME_COLUMN = 'CFF_Ad_Hoc_Client_Name'
CLIENT_COLUMN = 'CFF_Client'
BASE_OF_OPERATION_COLUMN = 'CFF_Base_of_Operation'

# Update all references to column names in the file to use these constants

def _normalize_text(value):
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    text = str(value).strip()
    if text.lower() in ['', 'nan', 'none']:
        return None
    return text.casefold()

def _normalize_takeoff_time(value):
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    text = str(value).strip()
    if text.lower() in ['', 'nan', 'none']:
        return None
    if ':' in text:
        parts = text.split(':')
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            text = f"{int(parts[0]):02d}{int(parts[1]):02d}"
    text = ''.join(ch for ch in text if ch.isdigit())
    if text == '':
        return None
    if len(text) <= 4:
        return text.zfill(4)
    return text

def _normalize_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if hasattr(value, 'date'):
        try:
            return value.date()
        except Exception:
            pass
    if isinstance(value, str):
        text = value.strip()
        if text.lower() in ['', 'nan', 'none']:
            return None
        for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d']:
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        try:
            return pd.to_datetime(text).date()
        except Exception:
            return None
    return None

def _normalize_float(value, default=0.0):
    if value is None:
        return default
    if isinstance(value, float) and pd.isna(value):
        return default
    if isinstance(value, str) and value.strip().lower() in ['', 'nan', 'none']:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

@anvil.server.callable
def flight_records():
    col_names = [c['name'] for c in app_tables.flights.list_columns()]
    return [dict(row) for row in app_tables.flights.search(q.fetch_only(*col_names))]

def save_file(data_list,source,file):
    """
    Uploads processed list of dicts into flights table.
    Ignores duplicate entries
    """
    # starts a logger text
    logger = ''
    logger += "\nStart compare: {t}".format(t=time.time())
    col_names = [c['name'] for c in app_tables.flights.list_columns()]
    
    db_1 = [dict(row) for row in app_tables.flights.search(q.fetch_only(*col_names))]
    logger += "\nTable size: {s}, time table -> list: {t}".format(s=len(db_1),t=time.time())
    if db_1 is None or len(db_1) == 0:
        app_tables.flights.add_rows(data_list)
        db_2 = data_list
    else:
        # Remove entries in db_2 that already exist in db_1, and de-duplicate within incoming data
        db_2 = data_list
        logger += "\nFile size pre-strip: {s}".format(s=len(db_2))
        
        # we have to check if it's in db_1 first
        for entry in db_2:
            entry['duplicate'] = de_deuplicate(entry,db_1)
        print("First dedupe complete\n{o} first time entries,\n{d} entries".format( \
            o=len([e for e in db_2 if not e['duplicate']]), \
                d=len([e for e in db_2 if e['duplicate']])))

        
        logger += "\nFile after strip: {s}, Time after strip: {t}".format(
            s=len(db_2),
            t=time.time(),
        )
    
        app_tables.flights.add_rows([d for d in db_2 if not d['duplicate']])
        logger += "\nCompleted, Rows uploaded: {u},\nRows saved: {s}".format(u=len(data_list),
                                                                         s=len(db_2))
    app_tables.logs.add_row(date=datetime.now(),
                           results=logger,
                           file=file,
                           source=source)
    
    return {
        'complete': True,
        'total_rows': len(data_list),
        'rows_processed': len([d for d in db_2 if not d.get('duplicate', False)]),
        'logger': logger
    }


@anvil.server.callable
def receive_file(file, rows_completed=0, source='upload'):
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
    except Exception as e:
        raise Exception(f"Error converting DataFrame to list of dictionaries: {str(e)}")
    
    # Process each entry to ensure proper data types and remove NaN values
    for entry in data_list:
        # Normalize Takeoff Time
        if TAKEOFF_TIME_COLUMN in entry:
            entry[TAKEOFF_TIME_COLUMN] = _normalize_takeoff_time(entry.get(TAKEOFF_TIME_COLUMN))
        
        # Normalize FltDate
        if FLT_DATE_COLUMN in entry:
            entry[FLT_DATE_COLUMN] = _normalize_date(entry.get(FLT_DATE_COLUMN))
        
        # Normalize Air Time and Block Time
        if AIR_TIME_COLUMN in entry:
            entry[AIR_TIME_COLUMN] = _normalize_float(entry.get(AIR_TIME_COLUMN))
        if BLOCK_TIME_COLUMN in entry:
            entry[BLOCK_TIME_COLUMN] = _normalize_float(entry.get(BLOCK_TIME_COLUMN))
    
    # Add all rows to the flights table
    return save_file(data_list,source=source,file=file)
    
    # return {
    #     'complete': True,
    #     'total_rows': len(data_list),
    #     'rows_processed': len(data_list)
    # }

@anvil.email.handle_message
def handle_incoming_emails(msg):
  print("email function working")
  if len(msg.attachments) > 0:
    for a in msg.attachments:
      print(a.name)
      receive_file(file=a,source='email')
  elif len(msg.inline_attachments) > 0:
    for k,a in msg.inline_attachments.items():
      print(a.name)
      receive_file(file=a,source='email')
  else:
    print("No attachments found")
  

@anvil.server.callable
def api_handler(dates=None):
  """
  Fetches flight data from AirMaestro API and loads it into the flights table.
  
  Args:
    dates: Optional tuple/list of (start_date, end_date) as datetime.date objects or strings.
           If None, defaults to previous 10 days.
           
  Returns:
    dict: {'complete': True/False, 'total_rows': int, 'rows_processed': int, 'latest_log_date': datetime}
  """
  # API credentials and base URL
  api_key = 'n93_J*(17NoW1Hojh!5w6,*7v8*Y*.6ruJ9*Y*09L1HLUa*b-78o-55($EsvN96M'
  base_url = 'https://starlite.airmaestro.net/api/reports/333'
  
  result = {'complete': False, 'total_rows': 0, 'rows_processed': 0, 'latest_log_date': None}
  
  # Handle date parameters
  if dates is None:
    # Default to previous 10 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=10)
  else:
    # Parse provided dates
    if isinstance(dates, (tuple, list)) and len(dates) == 2:
      start_date = dates[0]
      end_date = dates[1]
      
      # Convert strings to date objects if needed
      if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
      if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
      raise ValueError("dates must be a tuple/list of (start_date, end_date)")
  
  # Format dates as yyyy-mm-dd
  param765 = start_date.strftime('%Y-%m-%d')  # FltDate after or on
  param768 = end_date.strftime('%Y-%m-%d')    # FltDate before or on
  
  # Build the URL with parameters
  url = f"{base_url}?Param765={param765}&Param768={param768}&format=CSV&AsAttachment=False"
  
  # Make the API request with authorization header
#   try:
  response = anvil.http.request(
    url,
    method='GET',
    headers={'Authorization': api_key}
  )

  # Get bytes from the response
  if hasattr(response, 'get_bytes'):
    csv_bytes = response.get_bytes()
  else:
    csv_bytes = response.encode('utf-8') if isinstance(response, str) else response

  # Process the CSV data directly
  result = process_csv_data(csv_bytes, source='api')
    
  #   except Exception as e:
  # error_msg = f"Error fetching data from AirMaestro API: {str(e)}"
  # print(error_msg)
  
  # Always check for latest log date regardless of API call success
  try:
    logs = app_tables.logs.search(tables.order_by('date', ascending=False))[0]
    if logs:
      latest_log = dict(logs)
      result['latest_log_date'] = latest_log['date']
  except Exception as e:
    print(f"Error retrieving latest log date: {str(e)}")
  
  return result


def process_csv_data(csv_bytes, source='api'):
    """
    Internal function to process CSV data from bytes and load into flights table.
    
    Args:
        csv_bytes: CSV data as bytes
        source: Source of the data (e.g., 'api', 'upload', 'email')
        
    Returns:
        dict: {'complete': True, 'total_rows': int, 'rows_processed': int}
    """
    start_time = time.time()
  
#   try:
    # Read CSV with different encodings
    try:
        df = pd.read_csv(io.BytesIO(csv_bytes), encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(io.BytesIO(csv_bytes), encoding='latin-1')
        except Exception:
            df = pd.read_csv(io.BytesIO(csv_bytes), encoding='iso-8859-1')

    # Check if the first row looks like data instead of headers
    if df is not None and len(df) > 0:
        # If all column names are generic (Unnamed) or numeric, assume no headers
        unnamed_cols = sum(1 for col in df.columns if str(col).startswith('Unnamed') or isinstance(col, int))
        
        if unnamed_cols == len(df.columns):
            # No headers detected - read again without header row
            try:
                df = pd.read_csv(io.BytesIO(csv_bytes), encoding='utf-8', header=None)
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(io.BytesIO(csv_bytes), encoding='latin-1', header=None)
                except Exception:
                    df = pd.read_csv(io.BytesIO(csv_bytes), encoding='iso-8859-1', header=None)
            
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

    # Handle empty dataframe
    if df is None or df.empty:
        return {'complete': True, 'total_rows': 0, 'rows_processed': 0}

    # Replace NaN values with None for better JSON serialization
    df = df.where(pd.notnull(df), None)

    # Ensure all column names are strings
    df.columns = [str(col) for col in df.columns]

    # Convert all columns to strings to ensure consistency
    df = df.astype(str)


    # Convert to list of dictionaries
    try:
        data_list = df.to_dict('records')
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
        if FLT_DATE_COLUMN in entry and entry[FLT_DATE_COLUMN] is not None:
            try:
                # Handle various date formats
                date_value = entry[FLT_DATE_COLUMN]
                if isinstance(date_value, str):
                    # Try parsing common date formats
                    for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d']:
                        try:
                            entry[FLT_DATE_COLUMN] = datetime.strptime(date_value, fmt).date()
                            break
                        except ValueError:
                            continue
                    else:
                        # If no format matched, try pandas parser
                        entry[FLT_DATE_COLUMN] = pd.to_datetime(date_value).date()
                elif isinstance(date_value, datetime):
                    entry[FLT_DATE_COLUMN] = date_value.date()
                elif hasattr(date_value, 'date'):
                    entry[FLT_DATE_COLUMN] = date_value.date()
            except Exception:
                # If conversion fails, set to None
                entry[FLT_DATE_COLUMN] = None
        
        # Convert Air Time to float or 0.0 if None/NaN
        if AIR_TIME_COLUMN in entry:
            try:
                val = entry[AIR_TIME_COLUMN]
                if val is None or (isinstance(val, str) and val.strip().lower() in ['', 'nan', 'none']):
                    entry[AIR_TIME_COLUMN] = 0.0
                elif isinstance(val, float) and pd.isna(val):
                    entry[AIR_TIME_COLUMN] = 0.0
                else:
                    entry[AIR_TIME_COLUMN] = float(val)
            except (ValueError, TypeError):
                entry[AIR_TIME_COLUMN] = 0.0
        
        # Convert Block Time to float or 0.0 if None/NaN
        if BLOCK_TIME_COLUMN in entry:
            try:
                val = entry[BLOCK_TIME_COLUMN]
                if val is None or (isinstance(val, str) and val.strip().lower() in ['', 'nan', 'none']):
                    entry[BLOCK_TIME_COLUMN] = 0.0
                elif isinstance(val, float) and pd.isna(val):
                    entry[BLOCK_TIME_COLUMN] = 0.0
                else:
                    entry[BLOCK_TIME_COLUMN] = float(val)
            except (ValueError, TypeError):
                entry[BLOCK_TIME_COLUMN] = 0.0
        
        # Convert all other fields to strings (except None values)
        for key, value in entry.items():
            if key not in [FLT_DATE_COLUMN, AIR_TIME_COLUMN, BLOCK_TIME_COLUMN, TAKEOFF_TIME_COLUMN]:
                if value is not None:
                    entry[key] = str(value)

    # Load the new flights to the table
    return save_file(data_list,source=source)
        
    #   except Exception as e:
    #     error_msg = f"Error processing CSV data: {str(e)}"
    #     print(error_msg)
    #     raise Exception(error_msg)
  
def de_deuplicate(entry,orig):
    key_columns = [FLT_DATE_COLUMN, TAKEOFF_TIME_COLUMN, REGO_COLUMN]
    try:
        if orig is None or len(orig) == 0:
            return False
        else:
            return len([f for f in orig if f[FLT_DATE_COLUMN] == entry[FLT_DATE_COLUMN] and \
                _normalize_takeoff_time(f[TAKEOFF_TIME_COLUMN]) == _normalize_takeoff_time(entry[TAKEOFF_TIME_COLUMN]) and \
                    _normalize_text(f[REGO_COLUMN]) == _normalize_text(entry[REGO_COLUMN])] ) > 0
    except Exception as e:
        print("Error in de_deuplicate: {e}".format(e=str(e)))
        print(entry)
        return False
        
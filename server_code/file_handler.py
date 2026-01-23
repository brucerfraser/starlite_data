import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import pandas as pd
import io

@anvil.server.callable
def save_file(file, description):
    """Saves a file along with its description to the database."""
    app_tables.Flights.add_row(file=file, description=description)

@anvil.server.callable
def receive_file(file):
    """
    Processes Excel (.xls, .xlsx) or CSV files and converts to list of dictionaries.
    Handles missing headers by creating default column names.
    Prints first 10 rows to console.
    
    Args:
        file: Anvil Media object containing the uploaded file
        
    Returns:
        list: List of dictionaries representing the data
    """
    try:
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
        
        # Handle empty dataframe
        if df is None or len(df) == 0:
            print("Warning: File is empty or could not be read")
            return []
        
        # Replace NaN values with None for better JSON serialization
        df = df.where(pd.notnull(df), None)
        
        # Convert to list of dictionaries
        data_list = df.to_dict('records')
        
        # Print first 10 rows to console
        print(f"\n{'='*60}")
        print(f"File processed: {file.name if hasattr(file, 'name') else 'Unknown'}")
        print(f"Total rows: {len(data_list)}")
        print(f"Columns: {list(df.columns)}")
        print(f"{'='*60}")
        print("First 10 rows:")
        print(f"{'-'*60}")
        
        for i, row in enumerate(data_list[:10], 1):
            print(f"\nRow {i}:")
            for key, value in row.items():
                print(f"  {key}: {value}")
        
        print(f"{'='*60}\n")
        
        return data_list
        
    except Exception as e:
        error_msg = f"Error processing file: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)

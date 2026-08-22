import csv
import glob

def check_csvs():
    files = glob.glob('*.csv')
    total_confirmed = 0
    
    for f in files:
        try:
            with open(f, 'r') as file:
                reader = csv.DictReader(file)
                headers = reader.fieldnames
                if not headers: continue
                
                rows = list(reader)
                
                if 'status' in headers:
                    confirmed = sum(1 for row in rows if row.get('status') == 'CONFIRMED')
                    print(f"{f}: {len(rows)} rows, {confirmed} CONFIRMED")
                    total_confirmed += confirmed
                else:
                    print(f"{f}: {len(rows)} rows. Columns: {headers}")
        except Exception as e:
            pass
            
    print(f"Total CONFIRMED (from status column): {total_confirmed}")

if __name__ == "__main__":
    check_csvs()

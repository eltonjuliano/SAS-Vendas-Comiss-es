import glob
from parser.pdf_parser import extract_pdf_data
from services.commission import process_sales_dataframe

def test():
    pdfs = glob.glob("*.pdf")[:3]
    raw_data = []
    
    for p in pdfs:
        # Ignore term of lgpd
        if "termo" in p.lower():
            continue
        try:
            with open(p, "rb") as f:
                data = extract_pdf_data(f)
                print(f"Extracted from {p}:")
                print(data)
                raw_data.append(data)
        except Exception as e:
            print(f"Error {p}: {e}")
            
    df = process_sales_dataframe(raw_data)
    if not df.empty:
        print("\nProcessed Dataframe:")
        print(df[['date', 'customer', 'total_revenue', 'total_commission', 'total_tires']])
    else:
        print("Empty df.")

if __name__ == "__main__":
    test()

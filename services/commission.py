import pandas as pd

def calculate_commission(total_parts, total_services, total_tires):
    """
    Business Logic for Commission Calculation:
    1. Tires yield 1% commission.
    2. Services + Non-Tire Parts yield 2% commission.
    """
    # Ensure tires are subtracted from parts to not double count
    # Note: total_parts from the PDF generally INCLUDES tires,
    # so non_tire_parts = total_parts - total_tires
    
    non_tire_parts = max(0.0, total_parts - total_tires)
    
    commission_services_parts = (non_tire_parts + total_services) * 0.02
    commission_tires = total_tires * 0.01
    
    return {
        'non_tire_parts': non_tire_parts,
        'commission_services_parts': commission_services_parts,
        'commission_tires': commission_tires,
        'total_commission': commission_services_parts + commission_tires
    }

def process_sales_dataframe(data_list):
    """
    Receives a list of extracted dictionaries from PDFs
    and returns a pandas DataFrame with all calculated fields.
    """
    if not data_list:
        return pd.DataFrame()
        
    df = pd.DataFrame(data_list)
    
    # Apply calculations
    commissions = df.apply(
        lambda row: calculate_commission(
            row['total_parts'], 
            row['total_services'], 
            row['total_tires']
        ), 
        axis=1
    )
    
    # Expand the dict results into the dataframe
    commissions_df = pd.DataFrame(commissions.tolist(), index=df.index)
    df = pd.concat([df, commissions_df], axis=1)
    
    # Enhance DataFrame with 'year_month' for grouping
    # date column could be None if parsing failed
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['year_month'] = df['date'].dt.to_period('M')
    
    # Total revenue for the order
    df['total_revenue'] = df['total_parts'] + df['total_services']
    
    return df

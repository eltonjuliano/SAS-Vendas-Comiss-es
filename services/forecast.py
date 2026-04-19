import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

def generate_forecast(df):
    """
    Predicts end-of-month revenue and commissions using Linear Regression
    based on the current month's sales trajectory.
    """
    if df.empty:
        return None

    # Filter data for the current month being processed
    # We'll use the latest month in the dataset
    latest_month = df['year_month'].max()
    current_month_data = df[df['year_month'] == latest_month].copy()
    
    # Needs to be sorted by date
    current_month_data = current_month_data.sort_values('date')
    
    if len(current_month_data) < 2:
        return None # Not enough data points to do a regression
        
    # Group by date to get daily totals
    daily_sales = current_month_data.groupby('date').agg(
        daily_revenue=('total_revenue', 'sum'),
        daily_commission=('total_commission', 'sum')
    ).reset_index()
    
    # Calculate cumulative sums
    daily_sales['cum_revenue'] = daily_sales['daily_revenue'].cumsum()
    daily_sales['cum_commission'] = daily_sales['daily_commission'].cumsum()
    
    # Calculate day of month
    daily_sales['day'] = pd.to_datetime(daily_sales['date']).dt.day
    
    # Linear Regression for Revenue
    X = daily_sales[['day']].values
    y_rev = daily_sales['cum_revenue'].values
    y_comm = daily_sales['cum_commission'].values
    
    model_rev = LinearRegression().fit(X, y_rev)
    model_comm = LinearRegression().fit(X, y_comm)
    
    # Predict for end of month (approx 30 days)
    # We could find exactly how many days are in the latest_month, but let's assume 30 for simplicity
    days_in_month = latest_month.days_in_month
    
    predicted_rev = model_rev.predict(np.array([[days_in_month]]))[0]
    predicted_comm = model_comm.predict(np.array([[days_in_month]]))[0]
    
    # Format and return safely (no negative predictions)
    return {
        'month': str(latest_month),
        'projected_revenue': max(0.0, predicted_rev),
        'projected_commission': max(0.0, predicted_comm),
        'current_revenue': y_rev[-1],
        'current_commission': y_comm[-1]
    }

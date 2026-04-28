import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

def generate_forecast(df, start_date, end_date):
    """
    Predicts end-of-cycle revenue and commissions using Linear Regression
    based on the filtered data's sales trajectory.
    """
    if df.empty:
        return None

    # Certifique-se de que está ordenado
    current_cycle_data = df.copy().sort_values('date')
    
    if len(current_cycle_data) < 2:
        return None # Not enough data points
        
    # Group by date to get daily totals
    daily_sales = current_cycle_data.groupby('date').agg(
        daily_revenue=('total_revenue', 'sum'),
        daily_commission=('total_commission', 'sum')
    ).reset_index()
    
    # Calculate cumulative sums
    daily_sales['cum_revenue'] = daily_sales['daily_revenue'].cumsum()
    daily_sales['cum_commission'] = daily_sales['daily_commission'].cumsum()
    
    # Calculate day index (days since start_date)
    # Isso é melhor que 'dt.day' pois o ciclo atravessa meses.
    # Dia 1 do ciclo = start_date
    start_ts = pd.to_datetime(start_date)
    end_ts = pd.to_datetime(end_date)
    
    daily_sales['day_index'] = (pd.to_datetime(daily_sales['date']) - start_ts).dt.days + 1
    
    # Linear Regression for Revenue
    X = daily_sales[['day_index']].values
    y_rev = daily_sales['cum_revenue'].values
    y_comm = daily_sales['cum_commission'].values
    
    model_rev = LinearRegression().fit(X, y_rev)
    model_comm = LinearRegression().fit(X, y_comm)
    
    # Predict for end of cycle
    total_days_in_cycle = (end_ts - start_ts).days + 1
    if total_days_in_cycle <= 0:
        total_days_in_cycle = 30
        
    predicted_rev = model_rev.predict(np.array([[total_days_in_cycle]]))[0]
    predicted_comm = model_comm.predict(np.array([[total_days_in_cycle]]))[0]
    
    # Format and return safely (no negative predictions)
    return {
        'month': f"{start_ts.strftime('%d/%m/%Y')} a {end_ts.strftime('%d/%m/%Y')}",
        'projected_revenue': max(0.0, predicted_rev),
        'projected_commission': max(0.0, predicted_comm),
        'current_revenue': y_rev[-1] if len(y_rev) > 0 else 0,
        'current_commission': y_comm[-1] if len(y_comm) > 0 else 0
    }

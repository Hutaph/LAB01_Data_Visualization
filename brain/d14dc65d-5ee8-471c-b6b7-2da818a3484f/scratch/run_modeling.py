import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score
import warnings

warnings.filterwarnings('ignore')

# Load data
data_path = "d:/Schools/Data_Visualization/LAB01_Data_Visualization/LAB01_Data_Visualization/data/Processed/amazon_products_modeling.csv"
df = pd.read_csv(data_path)

# Split
X = df.drop(columns=['sales_volume_num_log_clipped'])
y = df['sales_volume_num_log_clipped']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Linear Regression
lr = LinearRegression()
lr.fit(X_train, y_train)
y_pred_lr = lr.predict(X_test)
rmse_lr = np.sqrt(mean_squared_error(y_test, y_pred_lr))
r2_lr = r2_score(y_test, y_pred_lr)

# Random Forest (simple run for info)
rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
y_pred_rf = rf.predict(X_test)
rmse_rf = np.sqrt(mean_squared_error(y_test, y_pred_rf))
r2_rf = r2_score(y_test, y_pred_rf)
rf_fi = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False).head(10)

# Gradient Boosting (simple run for info)
gb = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
gb.fit(X_train, y_train)
y_pred_gb = gb_model_pred = gb.predict(X_test)
rmse_gb = np.sqrt(mean_squared_error(y_test, y_pred_gb))
r2_gb = r2_score(y_test, y_pred_gb)
gb_fi = pd.Series(gb.feature_importances_, index=X.columns).sort_values(ascending=False).head(10)

print(f"LR: RMSE={rmse_lr:.4f}, R2={r2_lr:.4f}")
print(f"RF: RMSE={rmse_rf:.4f}, R2={r2_rf:.4f}")
print(f"GB: RMSE={rmse_gb:.4f}, R2={r2_gb:.4f}")
print(f"RF Top Features: {rf_fi.to_dict()}")
print(f"GB Top Features: {gb_fi.to_dict()}")

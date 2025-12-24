import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

# 读取数据
df = pd.read_csv('summerOly_medal_counts.csv', parse_dates=['Year'])
df = df.sort_values(by=['Country', 'Year']).reset_index(drop=True)


# 构建特征
def preprocess_data(df):
    # 生成对数GDP列
    df['lnGDP'] = np.log(df['GDP'] + 1e-5)  # 避免log(0)

    # 东道主效应虚拟变量（假设数据包含'IsHost'列，1表示东道主）
    df['HostEffect'] = df['IsHost'].astype(int)

    # 历史奖牌滑动平均（窗口=3届）
    df['Medal_MA3'] = df.groupby('Country')['TotalMedals'].transform(
        lambda x: x.rolling(window=3, min_periods=1).mean()
    )
    return df


df = preprocess_data(df)

# 提取某国家数据（示例：美国）
country = 'United States'
df_country = df[df['Country'] == country].set_index('Year')

# 定义目标变量和外生变量
y = df_country['TotalMedals']          # 总奖牌数
X_exog = df_country[['lnGDP', 'HostEffect']]  # 外生变量

# 划分训练集和测试集（假设预测2028年）
train = df_country[df_country.index < '2020-01-01']
test = df_country[df_country.index >= '2020-01-01']

# 训练ARIMAX(2,2,1)
model_arimax = ARIMA(
    endog=train['TotalMedals'],
    exog=train[['lnGDP', 'HostEffect']],
    order=(2,2,1)
)
result_arimax = model_arimax.fit()

# 预测2028年（需提供外生变量未来值）
future_exog = pd.DataFrame({
    'lnGDP': [np.log(25e12)],  # 假设2028年美国GDP为25万亿美元
    'HostEffect': [1]          # 2028年洛杉矶为东道主
}, index=pd.to_datetime(['2028-01-01']))

forecast = result_arimax.get_forecast(
    steps=1,
    exog=future_exog
)

# 输出结果
print(f"2028年预测奖牌数: {forecast.predicted_mean[0]:.1f}")
print(f"95%置信区间: {forecast.conf_int().values[0]}")

# 特征矩阵（示例：美国）
features = ['Medal_MA3', 'lnGDP', 'HostEffect']
X = df_country[features]
y = df_country['TotalMedals']

# 划分训练集和测试集
train_size = int(len(X) * 0.8)
X_train, X_test = X[:train_size], X[train_size:]
y_train, y_test = y[:train_size], y[train_size:]

# 训练随机森林
model_rf = RandomForestRegressor(
    n_estimators=100,
    max_depth=5,
    random_state=42
)
model_rf.fit(X_train, y_train)

# 预测与评估
y_pred = model_rf.predict(X_test)
print(f"MAE: {mean_absolute_error(y_test, y_pred):.2f}")
print(f"RMSE: {np.sqrt(mean_squared_error(y_test, y_pred)):.2f}")

# 预测2028年
future_features = pd.DataFrame({
    'Medal_MA3': [y_train[-3:].mean()],  # 近3届均值
    'lnGDP': [np.log(25e12)],
    'HostEffect': [1]
})
pred_2028 = model_rf.predict(future_features)
print(f"2028年随机森林预测奖牌数: {pred_2028[0]:.1f}")
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
import numpy as np
import matplotlib

# 设置后端和中文字体
matplotlib.use('TkAgg')
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 数据准备
data = pd.read_excel(r"D:\微信\WeChat Files\wxid_ca8uxz86bhhs22\FileStorage\File\2025-06\TOP250.xlsx")

# 数据预处理
# 检查数据
print(data.info())
print(data.head())

# 筛选需要的列
data = data[['上映年份', '评分']]

# 检查并处理缺失值
data.dropna(inplace=True)  # 删除缺失值
print(data.isnull().sum())  # 检查缺失值

# 数据分析
# 描述性统计
print(data.describe())

# 按年份分组，计算每年的平均评分
yearly_scores = data.groupby('上映年份')['评分'].mean()

# 计算相关系数
relation = data['上映年份'].corr(data['评分'])
print(f"相关系数: {relation}")

# 数据可视化
# 绘制每年平均评分的折线图
plt.figure(figsize=(10, 6))
plt.plot(yearly_scores.index, yearly_scores.values, marker='o')
plt.title('每年平均电影评分')
plt.xlabel('上映年份')
plt.ylabel('平均评分')
plt.grid(True)

# 显示图形
plt.tight_layout()  # 自动调整子图参数
plt.show()

# 进一步分析：线性回归
# 线性回归分析
X = data['上映年份'].values.reshape(-1, 1)
y = data['评分'].values
model = LinearRegression()
model.fit(X, y)

# 预测
years = np.arange(data['上映年份'].min(), data['上映年份'].max() + 1).reshape(-1, 1)
predicted_scores = model.predict(years)

# 绘制回归线
plt.figure(figsize=(10, 6))
plt.scatter(X, y, color='blue', label='实际评分')
plt.plot(years, predicted_scores, color='red', label='预测评分')
plt.title('电影评分与上映年份的线性回归')
plt.xlabel('上映年份')
plt.ylabel('评分')
plt.legend()
plt.show()

"""Вариант 9 без дополнительных библиотек и автоматических конвейеров.

Запускать из папки ml/ind: python3 ind9_basic.py
Используются pandas и matplotlib из ЛР2–3, а также линейная регрессия,
разделение выборки, K-fold и метрики из темы ЛР4 и индивидуального задания.
"""

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import KFold, train_test_split


# 1. Загрузка данных.
df = pd.read_csv("insurance.csv")
print("\n1. Данные загружены из insurance.csv")

# 2. Размер, типы, пропуски и повторы.
print("\n2. Предварительный анализ")
print("Размер:", df.shape)
print("Типы данных:\n", df.dtypes)
print("Пропуски:\n", df.isna().sum())
print("Полных повторов:", df.duplicated().sum())
df = df.drop_duplicates().reset_index(drop=True)

# 3. Проверка выбросов. Большие расходы сами по себе не являются ошибкой.
print("\n3. Проверка выбросов")
q1 = df["charges"].quantile(0.25)
q3 = df["charges"].quantile(0.75)
upper = q3 + 1.5 * (q3 - q1)
high = df["charges"] > upper
print(f"Верхняя граница по IQR: ${upper:.2f}")
print("Расходов выше границы:", high.sum())
print("Из них курящих:", ((df["smoker"] == "yes") & high).sum())
invalid = ((df["age"] <= 0) | (df["bmi"] <= 0) |
           (df["children"] < 0) | (df["charges"] <= 0))
print("Записей с невозможными числовыми значениями:", invalid.sum())
df = df.loc[~invalid].copy()
print("Высокие расходы сохранены, поскольку они не подтверждены как ошибки.")

# 4–5. Категории превращаются в столбцы 0/1 средствами pandas.
print("\n4–5. Числовое кодирование пола, региона и курения")
df["sex_male"] = (df["sex"] == "male").astype(int)
df["smoker_yes"] = (df["smoker"] == "yes").astype(int)
for region in ["northwest", "southeast", "southwest"]:
    df["region_" + region] = (df["region"] == region).astype(int)
print(df[["sex", "sex_male", "smoker", "smoker_yes", "region",
          "region_northwest", "region_southeast", "region_southwest"]].head())

# 6. Отложенная тестовая часть не используется при выборе признаков.
features = ["age", "bmi", "children", "sex_male", "smoker_yes",
            "region_northwest", "region_southeast", "region_southwest"]
X_train, X_test, y_train, y_test = train_test_split(
    df[features], df["charges"], test_size=0.30, random_state=42
)
print("\n6. Разделение: обучение", len(X_train), ", тест", len(X_test))

# 7. Распределение расходов.
print("\n7. Распределение расходов")
plt.figure(figsize=(8, 5))
plt.hist(y_train, bins=30, color="steelblue", edgecolor="white")
plt.title("Распределение медицинских расходов")
plt.xlabel("Расходы, $")
plt.ylabel("Количество клиентов")
plt.tight_layout()
plt.show()

# 8. Связь каждого исходного числового признака с расходами.
print("\n8. Связь числовых признаков с расходами")
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
for ax, column, title in zip(axes, ["age", "bmi", "children"],
                             ["Возраст", "Индекс массы тела", "Число детей"]):
    ax.scatter(X_train[column], y_train, alpha=0.35, s=12)
    ax.set_title(title)
    ax.set_xlabel(title)
    ax.set_ylabel("Расходы, $")
plt.tight_layout()
plt.show()

# 9–10. Корреляции вычисляются только на обучающих данных.
print("\n9–10. Корреляции и выбор признаков")
correlation_matrix = X_train.copy()
correlation_matrix["charges"] = y_train
correlation_matrix = correlation_matrix.corr()
print("Полная матрица корреляций (обучающая часть):")
rounded_matrix = correlation_matrix.round(2)
rounded_matrix = rounded_matrix.mask(rounded_matrix.abs() < 0.005, 0.0)
print(rounded_matrix.to_string())

fig, ax = plt.subplots(figsize=(10, 8))
picture = ax.imshow(correlation_matrix, cmap="coolwarm", vmin=-1, vmax=1)
ax.set_xticks(range(len(correlation_matrix.columns)))
ax.set_yticks(range(len(correlation_matrix.index)))
ax.set_xticklabels(correlation_matrix.columns, rotation=45, ha="right")
ax.set_yticklabels(correlation_matrix.index)
for row in range(len(correlation_matrix.index)):
    for column in range(len(correlation_matrix.columns)):
        value = rounded_matrix.iloc[row, column]
        color = "white" if abs(value) > 0.5 else "black"
        ax.text(column, row, f"{value:.2f}", ha="center", va="center",
                color=color, fontsize=8)
fig.colorbar(picture, ax=ax, label="Корреляция Пирсона")
ax.set_title("Матрица корреляций признаков и расходов")
plt.tight_layout()
plt.show()

correlations = X_train.apply(lambda column: column.corr(y_train))
print(correlations.sort_values(ascending=False).round(3))
selected = correlations.abs().sort_values(ascending=False).head(3).index.tolist()
print("Три наиболее связанных признака:", selected)
correlations.sort_values().plot(kind="barh", figsize=(8, 5))
plt.title("Корреляция признаков с расходами")
plt.xlabel("Корреляция Пирсона")
plt.tight_layout()
plt.show()

# 11–13. Пять раз обучаем модель на четырёх частях и проверяем на пятой.
# На каждом шаге выбираем признаки заново только по тренировочному фолду.
print("\n11–13. Линейная регрессия и K-fold")
cv = KFold(n_splits=5, shuffle=True, random_state=42)
mae_folds = []
r2_folds = []
for number, (train_index, check_index) in enumerate(cv.split(X_train), 1):
    X_fold_train = X_train.iloc[train_index]
    y_fold_train = y_train.iloc[train_index]
    X_fold_check = X_train.iloc[check_index]
    y_fold_check = y_train.iloc[check_index]
    fold_correlations = X_fold_train.apply(
        lambda column: column.corr(y_fold_train)
    )
    fold_features = fold_correlations.abs().sort_values(
        ascending=False
    ).head(3).index.tolist()
    fold_model = LinearRegression()
    fold_model.fit(X_fold_train[fold_features], y_fold_train)
    fold_prediction = fold_model.predict(X_fold_check[fold_features])
    mae = mean_absolute_error(y_fold_check, fold_prediction)
    r2 = r2_score(y_fold_check, fold_prediction)
    mae_folds.append(mae)
    r2_folds.append(r2)
    print(f"Фолд {number}: MAE = ${mae:.2f}, R² = {r2:.3f}")
print(f"Среднее по фолдам: MAE = ${sum(mae_folds) / 5:.2f}, "
      f"R² = {sum(r2_folds) / 5:.3f}")

model = LinearRegression()
model.fit(X_train[selected], y_train)
print("Коэффициенты итоговой модели:")
for name, value in zip(selected, model.coef_):
    print(f"  {name}: {value:.2f}")

# 14. Тест используется один раз для итоговой оценки.
print("\n14. Проверка на тестовом наборе")
prediction = model.predict(X_test[selected])
print(f"MAE = ${mean_absolute_error(y_test, prediction):.2f}")
print(f"R² = {r2_score(y_test, prediction):.3f}")
print(f"Пример: факт ${y_test.iloc[0]:.2f}, прогноз ${prediction[0]:.2f}")
plt.figure(figsize=(6, 5))
plt.scatter(y_test, prediction, alpha=0.4, s=15)
limits = [min(y_test.min(), prediction.min()),
          max(y_test.max(), prediction.max())]
plt.plot(limits, limits, "r--", label="Идеальный прогноз")
plt.title("Прогноз и фактические расходы")
plt.xlabel("Фактические расходы, $")
plt.ylabel("Прогноз, $")
plt.legend()
plt.tight_layout()
plt.show()

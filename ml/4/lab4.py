"""Лабораторная работа №4: линейная регрессия для AirQualityUCI.

Запуск из папки ml/4: python3 lab4.py
Нужны numpy, pandas и scikit-learn.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import KFold, train_test_split
from sklearn.preprocessing import PolynomialFeatures, StandardScaler


def fill_from_train(X_train_part, X_check_part):
    """Заполнить пропуски медианами обучающей части, не заглядывая в проверку."""
    medians = X_train_part.median()
    return X_train_part.fillna(medians), X_check_part.fillna(medians)


def scores(y_true, y_pred):
    return r2_score(y_true, y_pred), mean_squared_error(y_true, y_pred)


def print_scores(name, y_true, y_pred):
    r2, mse = scores(y_true, y_pred)
    print(f"{name}: R² = {r2:.4f}; MSE = {mse:.4f}")
    return name, r2, mse


def choose_alpha(X, y, model_type, alphas, folds):
    """Пять фолдов: в каждом отдельно вычислить медианы и стандартизацию."""
    results = []
    for alpha in alphas:
        errors = []
        for train_idx, check_idx in folds.split(X):
            X_part = X.iloc[train_idx]
            X_check = X.iloc[check_idx]
            y_part = y.iloc[train_idx]
            y_check = y.iloc[check_idx]
            X_part, X_check = fill_from_train(X_part, X_check)
            scaler = StandardScaler()
            X_part_scaled = scaler.fit_transform(X_part)
            X_check_scaled = scaler.transform(X_check)
            if model_type == "Lasso":
                model = Lasso(alpha=alpha, max_iter=30000)
            else:
                model = Ridge(alpha=alpha)
            model.fit(X_part_scaled, y_part)
            errors.append(mean_squared_error(y_check, model.predict(X_check_scaled)))
        results.append((alpha, np.mean(errors)))
    return min(results, key=lambda pair: pair[1])[0], results


df = pd.read_csv("AirQualityUCI.csv", sep=";", decimal=",", na_values=["-200"])
df = df.drop(columns=["Unnamed: 15", "Unnamed: 16"]).dropna(how="all")
df = df.dropna(subset=["CO(GT)"]).copy()
dates = pd.to_datetime(df["Date"], format="%d/%m/%Y")
df["day"] = (dates - dates.min()).dt.days
df["hour"] = df["Time"].str[:2].astype(int)

target = "CO(GT)"
single = ["C6H6(GT)"]
multiple = ["C6H6(GT)", "T", "RH", "NO2(GT)"]
all_features = [name for name in df.select_dtypes(include="number").columns
                if name != target]
X_train, X_test, y_train, y_test = train_test_split(
    df[all_features], df[target], test_size=0.30, random_state=42
)
results = []
print(f"Загружено {len(df)} строк с известным CO(GT). ")
print(f"Обучение: {len(X_train)} строк; тест: {len(X_test)} строк.")
print(f"Признаки для Lasso и Ridge ({len(all_features)}): {', '.join(all_features)}")
print("Пропуски в признаках заполняются медианами только обучающей части.")

# 1. Одна переменная: концентрация бензола.
print("\n1. Простая линейная регрессия")
X1_train, X1_test = fill_from_train(X_train[single], X_test[single])
simple_model = LinearRegression()
simple_model.fit(X1_train, y_train)
results.append(print_scores("Бензол", y_test, simple_model.predict(X1_test)))
print(f"Коэффициент бензола: {simple_model.coef_[0]:.4f}; "
      f"свободный член: {simple_model.intercept_:.4f}")

# 2. Четыре исходных измеряемых признака.
print("\n2. Множественная линейная регрессия")
X4_train, X4_test = fill_from_train(X_train[multiple], X_test[multiple])
multiple_model = LinearRegression()
multiple_model.fit(X4_train, y_train)
results.append(print_scores("Четыре признака", y_test,
                            multiple_model.predict(X4_test)))
for name, value in zip(multiple, multiple_model.coef_):
    print(f"  {name}: {value:.4f}")

# 3. Стандартизация: scaler обучается только на train.
print("\n3. Стандартизация и линейная регрессия")
scaler4 = StandardScaler()
X4_train_scaled = scaler4.fit_transform(X4_train)
X4_test_scaled = scaler4.transform(X4_test)
scaled_model = LinearRegression()
scaled_model.fit(X4_train_scaled, y_train)
results.append(print_scores("Четыре признака + StandardScaler", y_test,
                            scaled_model.predict(X4_test_scaled)))
print("Коэффициенты после стандартизации (за 1 стандартное отклонение):")
for name, value in zip(multiple, scaled_model.coef_):
    print(f"  {name}: {value:.4f}")

# Общий набор всех измерений + день и час для пунктов 4, 5 и 7.
X_all_train, X_all_test = fill_from_train(X_train, X_test)
scaler_all = StandardScaler()
X_all_train_scaled = scaler_all.fit_transform(X_all_train)
X_all_test_scaled = scaler_all.transform(X_all_test)
folds = KFold(n_splits=5, shuffle=True, random_state=42)
lasso_alphas = [0.0001, 0.001, 0.01, 0.03, 0.1, 0.3, 1.0]
ridge_alphas = [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0]

# 4. L1 регуляризация и подбор alpha на обучающих фолдах.
print("\n4. Lasso, L1 регуляризация")
lasso_alpha, lasso_search = choose_alpha(
    X_train, y_train, "Lasso", lasso_alphas, folds
)
lasso_model = Lasso(alpha=lasso_alpha, max_iter=30000)
lasso_model.fit(X_all_train_scaled, y_train)
results.append(print_scores("Lasso", y_test,
                            lasso_model.predict(X_all_test_scaled)))
print(f"Выбранная alpha: {lasso_alpha}")
print(f"Ненулевых коэффициентов: {np.count_nonzero(lasso_model.coef_)} "
      f"из {len(all_features)}")

# 5. L2 регуляризация и подбор alpha на тех же фолдах.
print("\n5. Ridge, L2 регуляризация")
ridge_alpha, ridge_search = choose_alpha(
    X_train, y_train, "Ridge", ridge_alphas, folds
)
ridge_model = Ridge(alpha=ridge_alpha)
ridge_model.fit(X_all_train_scaled, y_train)
results.append(print_scores("Ridge", y_test,
                            ridge_model.predict(X_all_test_scaled)))
print(f"Выбранная alpha: {ridge_alpha}")

# 6. K-fold для модели из пункта 2. Медианы в каждом фолде свои.
print("\n6. K-fold для множественной линейной регрессии")
cv_r2 = []
cv_mse = []
for number, (train_idx, check_idx) in enumerate(folds.split(X_train), 1):
    X_part = X_train[multiple].iloc[train_idx]
    X_check = X_train[multiple].iloc[check_idx]
    y_part = y_train.iloc[train_idx]
    y_check = y_train.iloc[check_idx]
    X_part, X_check = fill_from_train(X_part, X_check)
    model = LinearRegression()
    model.fit(X_part, y_part)
    r2, mse = scores(y_check, model.predict(X_check))
    cv_r2.append(r2)
    cv_mse.append(mse)
    print(f"Фолд {number}: R² = {r2:.4f}; MSE = {mse:.4f}")
print(f"Среднее по фолдам: R² = {np.mean(cv_r2):.4f}; "
      f"MSE = {np.mean(cv_mse):.4f}")

# 7. Подробности кросс-валидации для выбора alpha.
print("\n7. Выбор alpha по пяти фолдам")
for title, search, chosen in [("Lasso", lasso_search, lasso_alpha),
                              ("Ridge", ridge_search, ridge_alpha)]:
    print(title)
    for alpha, mse in search:
        print(f"  alpha = {alpha:g}: средняя MSE = {mse:.4f}")
    print(f"  Оптимальная alpha = {chosen:g}")
print("Качество выбранных моделей на тесте указано в пунктах 4 и 5.")

# 8. Квадратичные признаки из тех же четырёх переменных.
print("\n8. Полиномиальная регрессия степени 2")
poly = PolynomialFeatures(degree=2, include_bias=False)
X_poly_train = poly.fit_transform(X4_train)
X_poly_test = poly.transform(X4_test)
poly_model = LinearRegression()
poly_model.fit(X_poly_train, y_train)
results.append(print_scores("Полиномиальная степень 2", y_test,
                            poly_model.predict(X_poly_test)))
print("Сравнение с обычной моделью из пункта 2:")
print_scores("Обычная линейная регрессия", y_test,
             multiple_model.predict(X4_test))
print("Коэффициенты полиномиальной модели (в исходных единицах):")
for name, value in zip(poly.get_feature_names_out(multiple), poly_model.coef_):
    print(f"  {name}: {value:.4f}")

# 9. Сводная таблица и интерпретация коэффициентов.
print("\n9. Сравнение моделей на одном тестовом наборе")
print(f"{'Модель':38} {'R²':>9} {'MSE':>12}")
for name, r2, mse in results:
    print(f"{name:38} {r2:9.4f} {mse:12.4f}")
print("\nСтандартизованные коэффициенты Lasso и Ridge:")
for name, lasso_coef, ridge_coef in zip(
    all_features, lasso_model.coef_, ridge_model.coef_
):
    print(f"  {name:18} Lasso {lasso_coef:9.4f}  Ridge {ridge_coef:9.4f}")
print("Больший модуль стандартизованного коэффициента показывает более сильную "
      "связь внутри данной модели, но при коррелирующих признаках не доказывает "
      "причинное влияние.")
important = sorted(zip(all_features, ridge_model.coef_),
                   key=lambda pair: abs(pair[1]), reverse=True)[:3]
print("Наибольшие по модулю коэффициенты Ridge: " +
      ", ".join(f"{name} ({value:+.4f})" for name, value in important) + ".")
print("Коэффициенты полиномиальной модели имеют разные единицы измерения "
      "из-за квадратов и произведений; напрямую сравнивать их модули нельзя.")
best = max(results, key=lambda row: row[1])
print(f"На этом тесте наибольший R² у модели «{best[0]}»: {best[1]:.4f}.")

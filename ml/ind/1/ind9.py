"""Индивидуальное задание 9: прогноз расходов на медицинское страхование.

Запуск: python3 ind9.py (из любой папки). Результаты и рисунки сохраняются
в results рядом со скриптом. Нужны pandas, numpy, matplotlib, scikit-learn.
"""

from pathlib import Path
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import KFold, cross_validate, train_test_split
from sklearn.pipeline import make_pipeline


HERE = Path(__file__).resolve().parent
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
RANDOM_STATE = 42
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})


def save_figure(name):
    plt.tight_layout()
    plt.savefig(OUT / name, dpi=160, bbox_inches="tight")
    plt.close()


def main():
    # 1–2. Загрузка и предварительный анализ.
    df = pd.read_csv(HERE / "insurance.csv")
    print("1–2. Загрузка и предварительный анализ")
    print(f"Размер исходного набора: {df.shape[0]} строк, {df.shape[1]} столбцов")
    print("Типы данных:\n", df.dtypes.to_string())
    print("Пропуски:\n", df.isna().sum().to_string())
    duplicates = int(df.duplicated().sum())
    print("Полных повторов:", duplicates)
    df = df.drop_duplicates().reset_index(drop=True)

    # 3. Выбросы: граница IQR служит сигналом для проверки, а не правилом удаления.
    print("\n3. Проверка выбросов")
    q1, q3 = df["charges"].quantile([0.25, 0.75])
    high_limit = q3 + 1.5 * (q3 - q1)
    high = df["charges"] > high_limit
    high_count = int(high.sum())
    high_smokers = int((high & df["smoker"].eq("yes")).sum())
    invalid = (
        df["age"].le(0) | df["bmi"].le(0) | df["children"].lt(0)
        | df["charges"].le(0)
    )
    print(f"Граница IQR по расходам: ${high_limit:,.2f}")
    print(f"Выше границы: {high_count}, из них курящих: {high_smokers}")
    print("Строк с невозможными числовыми значениями:", int(invalid.sum()))
    df = df.loc[~invalid].copy()
    print("Высокие расходы сохранены: они могут быть реальными наблюдениями.")

    # 4–5. Кодирование категорий без фиктивного порядка между регионами.
    print("\n4–5. Преобразование категориальных признаков")
    encoded = pd.get_dummies(
        df.drop(columns="charges"), columns=["sex", "smoker", "region"],
        drop_first=True, dtype=int,
    )
    print("Столбцы после кодирования:", ", ".join(encoded.columns))

    # 6. Отложенный тест: изучать корреляции и выбирать признаки можно лишь на train.
    X_train, X_test, y_train, y_test = train_test_split(
        encoded, df["charges"], test_size=0.30, random_state=RANDOM_STATE
    )
    print("\n6. Разделение данных")
    print(f"Обучающая часть: {len(X_train)}, тестовая: {len(X_test)}")

    # 7–8. Исследовательские графики. Для связей с расходами используется train.
    print("\n7–8. Графики распределения и связей сохранены в results/")
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.hist(y_train, bins=30, color="#4778a9", edgecolor="white")
    ax.set(title="Распределение расходов в обучающей части",
           xlabel="Расходы, $", ylabel="Число клиентов")
    save_figure("01_charges_hist.png")

    fig, axs = plt.subplots(2, 2, figsize=(10, 7))
    for ax, col, label in zip(axs.flat, ["age", "bmi", "children", "smoker_yes"],
                              ["Возраст, лет", "ИМТ", "Число детей", "Курение (0 — нет, 1 — да)"]):
        ax.scatter(X_train[col], y_train, alpha=.35, s=13, color="#4778a9")
        ax.set(xlabel=label, ylabel="Расходы, $")
    fig.suptitle("Связь числовых признаков и расходов")
    save_figure("02_features_scatter.png")

    # 9–10. Корреляции и отбор трёх сильнейших признаков только по train.
    correlations = X_train.apply(lambda col: col.corr(y_train)).sort_values(key=abs, ascending=False)
    selected = correlations.head(3).index.tolist()
    print("\n9–10. Корреляция признаков с расходами на обучающей части")
    print(correlations.round(3).to_string())
    print("Три выбранных признака:", ", ".join(selected))
    fig, ax = plt.subplots(figsize=(8, 4.8))
    correlations.sort_values().plot.barh(ax=ax, color="#4778a9")
    ax.set(xlabel="Коэффициент корреляции Пирсона", title="Корреляция с расходами (train)")
    ax.axvline(0, color="black", linewidth=.6)
    save_figure("03_correlations.png")

    # 11–13. Модель и кросс-валидация строго внутри обучающей части.
    print("\n11–13. Линейная регрессия и кросс-валидация")
    model = LinearRegression()
    cv = KFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    # На каждом фолде признаки отбираются заново, без просмотра проверочной части.
    cv_model = make_pipeline(SelectKBest(f_regression, k=3), LinearRegression())
    scores = cross_validate(
        cv_model, X_train, y_train, cv=cv,
        scoring={"mae": "neg_mean_absolute_error", "r2": "r2"},
    )
    cv_mae = -scores["test_mae"]
    cv_r2 = scores["test_r2"]
    print(f"CV MAE: ${cv_mae.mean():,.2f} ± ${cv_mae.std():,.2f}")
    print(f"CV R²: {cv_r2.mean():.3f} ± {cv_r2.std():.3f}")
    model.fit(X_train[selected], y_train)
    print("Свободный член:", round(float(model.intercept_), 2))
    print("Коэффициенты:", {name: round(float(value), 2)
                            for name, value in zip(selected, model.coef_)})

    # 14. Итоговая проверка на ранее не использованном тесте.
    print("\n14. Проверка на тестовом наборе")
    prediction = model.predict(X_test[selected])
    test_mae = mean_absolute_error(y_test, prediction)
    test_r2 = r2_score(y_test, prediction)
    print(f"Тест MAE: ${test_mae:,.2f}; R²: {test_r2:.3f}")
    print(f"Пример: фактически ${y_test.iloc[0]:,.2f}, прогноз ${prediction[0]:,.2f}")
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(y_test, prediction, alpha=.45, s=17, color="#4778a9")
    bounds = [min(y_test.min(), prediction.min()), max(y_test.max(), prediction.max())]
    ax.plot(bounds, bounds, color="#c44e52", linestyle="--", label="Идеальный прогноз")
    ax.set(xlabel="Фактические расходы, $", ylabel="Прогноз, $",
           title="Предсказания на тестовой части")
    ax.legend()
    save_figure("04_predictions.png")

    result = {
        "original_rows": len(df) + duplicates + int(invalid.sum()),
        "duplicates_removed": duplicates,
        "rows_after_cleaning": len(df), "missing_total": int(df.isna().sum().sum()),
        "iqr_upper_charges": high_limit, "iqr_high_count": high_count,
        "iqr_high_smokers": high_smokers, "invalid_rows_removed": int(invalid.sum()),
        "train_rows": len(X_train), "test_rows": len(X_test),
        "correlations_train": correlations.to_dict(), "selected_features": selected,
        "cv_mae_folds": cv_mae.tolist(), "cv_r2_folds": cv_r2.tolist(),
        "cv_mae_mean": cv_mae.mean(), "cv_r2_mean": cv_r2.mean(),
        "intercept": model.intercept_, "coefficients": dict(zip(selected, model.coef_)),
        "test_mae": test_mae, "test_r2": test_r2,
        "example_actual": y_test.iloc[0], "example_prediction": prediction[0],
    }
    (OUT / "metrics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=float), encoding="utf-8"
    )


if __name__ == "__main__":
    main()

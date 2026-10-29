from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import BernoulliNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.tree import DecisionTreeClassifier, plot_tree


HERE = Path(__file__).resolve().parent
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
RANDOM_STATE = 42
GILL_COLUMNS = ["gill-attachment", "gill-spacing", "gill-size"]


def models(task_number):
    result = {
        "Логистическая регрессия": LogisticRegression(max_iter=2000),
        "Дерево решений": DecisionTreeClassifier(
            random_state=RANDOM_STATE, min_samples_leaf=2
        ),
        "Случайный лес": RandomForestClassifier(
            n_estimators=100, random_state=RANDOM_STATE, n_jobs=2
        ),
    }
    if task_number >= 2:
        result["Градиентный бустинг"] = HistGradientBoostingClassifier(
            max_iter=80, max_leaf_nodes=15, random_state=RANDOM_STATE
        )
        result["Наивный Байес"] = BernoulliNB()
    if task_number == 3:
        result["K ближайших соседей"] = KNeighborsClassifier(n_neighbors=5, n_jobs=2)
    return result


def show_confusion(matrix, labels, task_key, model_key, description, model_name):
    fig, ax = plt.subplots(figsize=(max(5, len(labels) + 2), max(4, len(labels) + 1)))
    image = ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(range(len(labels)), labels=labels, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)), labels=labels)
    ax.set(xlabel="Предсказанный класс", ylabel="Фактический класс",
           title=f"{description}\nМатрица ошибок: {model_name}")
    for row in range(len(labels)):
        for column in range(len(labels)):
            value = matrix[row, column]
            color = "white" if value > matrix.max() / 2 else "black"
            ax.text(column, row, str(value), ha="center", va="center", color=color)
    fig.colorbar(image, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(OUT / f"{task_key}_{model_key}_confusion.png", dpi=140)
    plt.close(fig)


def show_tree(model, feature_names, labels, task_key, description):
    fig, ax = plt.subplots(figsize=(18, 9))
    plot_tree(
        model, max_depth=3, feature_names=feature_names,
        class_names=labels, filled=True, rounded=True, fontsize=7, ax=ax,
    )
    ax.set_title(f"{description}\nДерево решений: первые четыре уровня")
    fig.tight_layout()
    fig.savefig(OUT / f"{task_key}_tree.png", dpi=150)
    plt.close(fig)


def run_task(df, number, task_key, description, target, excluded, positive=None):
    print(f"\n{number}. {description}", flush=True)
    feature_columns = [column for column in df.columns if column not in excluded]
    X = df[feature_columns]
    encoder = LabelEncoder()
    y = encoder.fit_transform(target)
    labels = list(encoder.classes_)
    print("Количество объектов по классам:")
    print(pd.Series(np.bincount(y), index=labels).to_string())
    print(f"Признаков до кодирования: {len(feature_columns)}")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=RANDOM_STATE
    )
    # Кодировщик изучает категории только в обучающей части.
    one_hot = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    X_train_encoded = one_hot.fit_transform(X_train)
    X_test_encoded = one_hot.transform(X_test)
    print(f"Обучение: {len(X_train)}; тест: {len(X_test)}; "
          f"столбцов после кодирования: {X_train_encoded.shape[1]}")
    if positive is not None:
        positive_code = int(encoder.transform([positive])[0])
        print(f"Положительный класс для Precision, Recall, F1 и AUC: {positive}")

    records = []
    for model_key, model in models(int(number.split(".")[0])).items():
        print(f"\nМодель: {model_key}", flush=True)
        model.fit(X_train_encoded, y_train)
        predicted = model.predict(X_test_encoded)
        probabilities = model.predict_proba(X_test_encoded)
        if len(labels) == 2:
            average = "binary"
            precision = precision_score(y_test, predicted, average=average,
                                        pos_label=positive_code, zero_division=0)
            recall = recall_score(y_test, predicted, average=average,
                                  pos_label=positive_code, zero_division=0)
            f1 = f1_score(y_test, predicted, average=average,
                          pos_label=positive_code, zero_division=0)
            positive_index = list(model.classes_).index(positive_code)
            auc = roc_auc_score(y_test == positive_code,
                                probabilities[:, positive_index])
        else:
            precision = precision_score(y_test, predicted, average="weighted",
                                        zero_division=0)
            recall = recall_score(y_test, predicted, average="weighted",
                                  zero_division=0)
            f1 = f1_score(y_test, predicted, average="weighted", zero_division=0)
            auc = roc_auc_score(y_test, probabilities, labels=model.classes_,
                                multi_class="ovr", average="weighted")
        accuracy = accuracy_score(y_test, predicted)
        matrix = confusion_matrix(y_test, predicted, labels=model.classes_)
        safe_model_key = {
            "Логистическая регрессия": "logistic",
            "Дерево решений": "tree",
            "Случайный лес": "forest",
            "Градиентный бустинг": "boosting",
            "Наивный Байес": "bayes",
            "K ближайших соседей": "knn",
        }[model_key]
        show_confusion(matrix, labels, task_key, safe_model_key,
                       description, model_key)
        if model_key == "Дерево решений":
            show_tree(model, one_hot.get_feature_names_out(feature_columns),
                      labels, task_key, description)
        print(f"  Accuracy = {accuracy:.4f}; Precision = {precision:.4f}; "
              f"Recall = {recall:.4f}; F1 = {f1:.4f}; AUC-ROC = {auc:.4f}")
        print("  Матрица ошибок (строки — факт, столбцы — прогноз):")
        print(pd.DataFrame(matrix, index=labels, columns=labels).to_string())
        records.append({
            "Задача": task_key, "Модель": model_key,
            "Accuracy": accuracy, "Precision": precision,
            "Recall": recall, "F1": f1, "AUC-ROC": auc,
        })
    return records


if __name__ == "__main__":
    # 0
    print("\n0. Предварительный анализ данных")
    df = pd.read_csv(HERE / "mushrooms.csv", na_values=["?"])
    print(f"Размер: {df.shape[0]} строки, {df.shape[1]} столбца")
    print("Типы данных:\n" + df.dtypes.to_string())
    print("Пропуски:\n" + df.isna().sum().to_string())
    print("Полных повторов:", int(df.duplicated().sum()))
    print("Уникальных значений:\n" + df.nunique(dropna=False).to_string())
    print("Распределение съедобности:\n" + df["class"].value_counts().to_string())
    print("Распределение местообитаний:\n" + df["habitat"].value_counts().to_string())
    print("Неизвестный stalk-root сохранён как отдельная категория 'missing'.")
    df = df.fillna("missing")

    # 1
    all_records = run_task(
        df, "1", "edibility", "Определение съедобности гриба",
        df["class"], ["class"], positive="p",
    )

    # 2
    all_records += run_task(
        df, "2", "habitat", "Предсказание типа местообитания гриба",
        df["habitat"], ["habitat"],
    )

    # 3
    # Все три целевых признака пластинок исключаем из входных данных.
    print("\n3. Предсказание структуры пластинок")

    # 3.1
    all_records += run_task(
        df, "3.1", "gill_attachment", "Прикрепление пластинок",
        df["gill-attachment"], GILL_COLUMNS, positive="a",
    )

    # 3.2
    all_records += run_task(
        df, "3.2", "gill_spacing", "Расстояние между пластинками",
        df["gill-spacing"], GILL_COLUMNS, positive="w",
    )

    # 3.3
    all_records += run_task(
        df, "3.3", "gill_size", "Размер пластинок",
        df["gill-size"], GILL_COLUMNS, positive="n",
    )

    # 3.4
    combined = df[GILL_COLUMNS].agg("|".join, axis=1)
    all_records += run_task(
        df, "3.4", "gill_combined", "Три характеристики пластинок вместе",
        combined, GILL_COLUMNS,
    )

    # 4
    print("\n4. Сравнение моделей")
    summary = pd.DataFrame(all_records)
    summary.to_csv(OUT / "metrics.csv", index=False, float_format="%.4f")
    summary_for_print = summary.copy()
    summary_for_print["Задача"] = summary_for_print["Задача"].replace({
        "edibility": "1. Съедобность",
        "habitat": "2. Местообитание",
        "gill_attachment": "3.1 Прикрепление пластинок",
        "gill_spacing": "3.2 Расстояние между пластинками",
        "gill_size": "3.3 Размер пластинок",
        "gill_combined": "3.4 Три признака пластинок",
    })
    print(summary_for_print.round(4).to_string(index=False))
    print(f"\nСохранено в {OUT}: metrics.csv, матрицы ошибок и рисунки деревьев.")
    print("Для многоклассовых задач Precision, Recall и F1 усреднены с весами "
          "по числу объектов каждого класса; AUC-ROC рассчитана One-vs-Rest.")

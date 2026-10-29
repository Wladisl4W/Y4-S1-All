from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_curve,
    auc,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC


def prepare_features(X_train, X_check):
    """Заполнить пропуски и стандартизовать по обучающей части."""
    medians = X_train.median()
    X_train = X_train.fillna(medians)
    X_check = X_check.fillna(medians)
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_check = scaler.transform(X_check)
    return X_train, X_check


def make_model(name, parameter):
    if name == "Логистическая регрессия":
        return LogisticRegression(C=parameter, max_iter=2000)
    if name == "Метод опорных векторов":
        return SVC(C=parameter, decision_function_shape="ovr", random_state=42)
    return RandomForestClassifier(
        n_estimators=parameter, random_state=42, n_jobs=-1
    )


def choose_parameter(name, parameters, X_train, y_train):
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    best_parameter = None
    best_score = -1
    for parameter in parameters:
        scores = []
        for train_index, check_index in folds.split(X_train, y_train):
            X_part = X_train.iloc[train_index]
            X_check = X_train.iloc[check_index]
            y_part = y_train.iloc[train_index]
            y_check = y_train.iloc[check_index]
            X_part, X_check = prepare_features(X_part, X_check)
            model = make_model(name, parameter)
            model.fit(X_part, y_part)
            predicted = model.predict(X_check)
            scores.append(f1_score(y_check, predicted, average="macro",
                                   zero_division=0))
        mean_score = sum(scores) / len(scores)
        print(f"  Параметр {parameter}: средняя F1 = {mean_score:.3f}")
        if mean_score > best_score:
            best_score = mean_score
            best_parameter = parameter
    return best_parameter, best_score


def show_confusion(y_true, y_pred, labels, name):
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    print("Матрица ошибок (строки — реальные оценки, столбцы — прогноз):")
    print(pd.DataFrame(matrix, index=labels, columns=labels).to_string())
    fig, ax = plt.subplots(figsize=(6, 5))
    picture = ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(range(len(labels)), labels=labels)
    ax.set_yticks(range(len(labels)), labels=labels)
    ax.set_xlabel("Предсказанная оценка качества")
    ax.set_ylabel("Реальная оценка качества")
    ax.set_title(f"Матрица ошибок: {name}")
    for row in range(len(labels)):
        for column in range(len(labels)):
            value = matrix[row, column]
            color = "white" if value > matrix.max() / 2 else "black"
            ax.text(column, row, str(value), ha="center", va="center",
                    color=color)
    fig.colorbar(picture, ax=ax)
    fig.tight_layout()


def show_roc(y_true, class_scores, labels, name):
    plt.figure(figsize=(7, 6))
    for column, quality in enumerate(labels):
        true_binary = (y_true == quality).astype(int)
        false_positive, true_positive, _ = roc_curve(
            true_binary, class_scores[:, column]
        )
        area = auc(false_positive, true_positive)
        plt.plot(false_positive, true_positive,
                 label=f"Оценка {quality} против остальных: AUC = {area:.3f}")
        print(f"  AUC-ROC для оценки {quality}: {area:.3f}")
    plt.plot([0, 1], [0, 1], "k--", label="Случайный прогноз")
    plt.title(f"ROC-кривые: {name}")
    plt.xlabel("Доля ложноположительных ответов")
    plt.ylabel("Доля верноположительных ответов")
    plt.legend(fontsize=8)
    plt.tight_layout()


if __name__ == "__main__":
    # 1
    print("\n1. Предварительная обработка данных")
    df = pd.read_csv(Path(__file__).resolve().parent / "winequality-red.csv", sep=";")
    print("Размер исходного набора:", df.shape)
    print("Типы данных:\n", df.dtypes)
    print("Пропуски:\n", df.isna().sum())
    print("Полных повторов:", df.duplicated().sum())
    df = df.drop_duplicates().reset_index(drop=True)
    print("После удаления повторов:", df.shape)
    print("Число вин по оценкам качества:\n", df["quality"].value_counts().sort_index())

    features = df.columns.drop("quality").tolist()
    X_train, X_test, y_train, y_test = train_test_split(
        df[features], df["quality"], test_size=0.30,
        stratify=df["quality"], random_state=42
    )
    labels = sorted(df["quality"].unique())
    print("Обучающих строк:", len(X_train), "тестовых строк:", len(X_test))
    print("Классы в обучении:", [int(value) for value in sorted(y_train.unique())])
    print("Классы в тесте:", [int(value) for value in sorted(y_test.unique())])
    X_train_scaled, X_test_scaled = prepare_features(X_train, X_test)
    print("Пропуски заполнены медианами обучения; признаки стандартизованы по обучению.")

    # 2
    print("\n2. Визуализация данных")
    X_train.hist(bins=20, figsize=(15, 11), edgecolor="black")
    plt.suptitle("Распределение химических признаков красного вина")
    plt.tight_layout()

    train_with_quality = X_train.copy()
    train_with_quality["quality"] = y_train
    correlations = train_with_quality.corr()
    print("Матрица корреляций (только обучающая часть):")
    print(correlations.round(2).to_string())
    fig, ax = plt.subplots(figsize=(11, 9))
    picture = ax.imshow(correlations, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(correlations.columns)), labels=correlations.columns,
                  rotation=45, ha="right")
    ax.set_yticks(range(len(correlations.index)), labels=correlations.index)
    for row in range(len(correlations.index)):
        for column in range(len(correlations.columns)):
            value = correlations.iloc[row, column]
            ax.text(column, row, f"{value:.2f}", ha="center", va="center",
                    fontsize=7, color="white" if abs(value) > 0.5 else "black")
    fig.colorbar(picture, ax=ax, label="Корреляция Пирсона")
    ax.set_title("Матрица корреляций признаков и качества вина")
    fig.tight_layout()

    important = (correlations["quality"].drop("quality").abs()
                 .sort_values(ascending=False).head(2).index.tolist())
    print("Два признака с наибольшей связью с качеством:", important)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for ax, feature in zip(axes, important):
        ax.scatter(X_train[feature], y_train, alpha=0.3, s=14)
        ax.set_title(f"Качество и {feature}")
        ax.set_xlabel(feature)
        ax.set_ylabel("Оценка качества")
    fig.tight_layout()

    # 3
    print("\n3. Классификация и подбор параметров")
    settings = [
        ("Логистическая регрессия", [0.1, 1, 10], "C"),
        ("Метод опорных векторов", [0.1, 1, 10], "C"),
        ("Случайный лес", [50, 100, 200], "число деревьев"),
    ]
    results = []
    for name, parameters, parameter_name in settings:
        print(f"\nМодель: {name}")
        best_parameter, cv_score = choose_parameter(
            name, parameters, X_train, y_train
        )
        print(f"Выбран параметр {parameter_name} = {best_parameter}; "
              f"средняя F1 на обучающих фолдах = {cv_score:.3f}")
        model = make_model(name, best_parameter)
        model.fit(X_train_scaled, y_train)
        predicted = model.predict(X_test_scaled)
        if name == "Метод опорных векторов":
            class_scores = model.decision_function(X_test_scaled)
        else:
            class_scores = model.predict_proba(X_test_scaled)
        accuracy = accuracy_score(y_test, predicted)
        precision = precision_score(y_test, predicted, average="macro",
                                    zero_division=0)
        recall = recall_score(y_test, predicted, average="macro", zero_division=0)
        f1 = f1_score(y_test, predicted, average="macro", zero_division=0)
        print(f"Тест: Accuracy = {accuracy:.3f}; Precision = {precision:.3f}; "
              f"Recall = {recall:.3f}; F1 = {f1:.3f}")
        show_confusion(y_test, predicted, labels, name)
        show_roc(y_test, class_scores, labels, name)
        results.append((name, best_parameter, accuracy, precision, recall, f1))

    # 4
    print("\n4. Сравнение классификаторов на одном тестовом наборе")
    print(f"{'Модель':27} {'Параметр':>10} {'Accuracy':>9} "
          f"{'Precision':>10} {'Recall':>8} {'F1':>8}")
    for name, parameter, accuracy, precision, recall, f1 in results:
        print(f"{name:27} {parameter:>10} {accuracy:9.3f} "
              f"{precision:10.3f} {recall:8.3f} {f1:8.3f}")
    print("Precision, Recall и F1 усреднены поровну по шести классам качества.")
    if plt.get_backend().lower() != "agg":
        plt.show()

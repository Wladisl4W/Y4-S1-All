from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, DBSCAN, KMeans
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler


def print_metrics(name, data, labels, exclude_noise=False):
    if exclude_noise:
        mask = labels != -1
        data = data[mask]
        labels = labels[mask]
    clusters = set(labels)
    if len(clusters) < 2 or len(labels) <= len(clusters):
        print(f"{name}: метрики не вычисляются — найдено меньше двух кластеров.")
        return
    silhouette = silhouette_score(data, labels)
    davies = davies_bouldin_score(data, labels)
    calinski = calinski_harabasz_score(data, labels)
    note = " (без шумовых точек)" if exclude_noise else ""
    print(f"{name}{note}: силуэт = {silhouette:.3f}; "
          f"Дэвис — Болдин = {davies:.3f}; "
          f"Калинский — Харабас = {calinski:.1f}")


def show_clusters(df, labels, name):
    fig = plt.figure(figsize=(14, 6))
    ax2d = fig.add_subplot(1, 2, 1)
    ax3d = fig.add_subplot(1, 2, 2, projection="3d")
    colors = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple"]

    for number, cluster in enumerate(sorted(set(labels))):
        group = df[labels == cluster]
        color = "gray" if cluster == -1 else colors[number % len(colors)]
        title = "Шум" if cluster == -1 else f"Кластер {cluster}"
        ax2d.scatter(group["Annual Income ($)"], group["Spending Score (1-100)"],
                     label=title, color=color, alpha=0.55, s=15)
        ax3d.scatter(group["Annual Income ($)"], group["Spending Score (1-100)"],
                     group["Age"], label=title, color=color, alpha=0.55, s=12)

    ax2d.set_title("2D: доход и оценка трат")
    ax2d.set_xlabel("Годовой доход, $")
    ax2d.set_ylabel("Оценка трат (0–100)")
    ax2d.legend()
    ax3d.set_title("3D: доход, траты и возраст")
    ax3d.set_xlabel("Доход, $")
    ax3d.set_ylabel("Оценка трат")
    ax3d.set_zlabel("Возраст, лет")
    ax3d.legend()
    fig.suptitle(f"Кластеризация клиентов: {name}")
    fig.tight_layout()


if __name__ == "__main__":
    # 0
    print("\n0. Предварительный анализ данных")
    df = pd.read_csv(Path(__file__).resolve().parent / "Customers2.csv")
    print("Размер:", df.shape)
    print("Типы данных:\n", df.dtypes)
    print("Пропуски:\n", df.isna().sum())
    print("Полных повторов:", df.duplicated().sum())
    print("Число клиентов по полу:\n", df["Gender"].value_counts())
    print("Описание числовых признаков:\n", df.describe().round(2))
    print("Пропуски в профессии не влияют на выбранные четыре признака.")

    data = df[["Gender", "Age", "Annual Income ($)",
               "Spending Score (1-100)"]].copy()
    data["Gender"] = data["Gender"].map({"Female": 0, "Male": 1})
    if data.isna().any().any():
        data = data.fillna(data.median())
    scaled = StandardScaler().fit_transform(data)
    print("Для кластеризации взяты: пол, возраст, доход и оценка трат.")
    print("Пол: Female = 0, Male = 1. Признаки стандартизованы.")

    # 1
    print("\n1. Выбор количества кластеров для K-means")
    cluster_counts = range(2, 9)
    inertias = []
    silhouettes = []
    for count in cluster_counts:
        model = KMeans(n_clusters=count, random_state=42, n_init=10)
        labels = model.fit_predict(scaled)
        inertia = model.inertia_
        silhouette = silhouette_score(scaled, labels)
        inertias.append(inertia)
        silhouettes.append(silhouette)
        print(f"k = {count}: сумма квадратов расстояний = {inertia:.1f}; "
              f"силуэт = {silhouette:.3f}")
    best_count = list(cluster_counts)[silhouettes.index(max(silhouettes))]
    print("Выбрано кластеров по наибольшему силуэту:", best_count)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].plot(list(cluster_counts), inertias, marker="o")
    axes[0].set_title("Метод локтя")
    axes[0].set_xlabel("Количество кластеров")
    axes[0].set_ylabel("Сумма квадратов расстояний")
    axes[1].plot(list(cluster_counts), silhouettes, marker="o")
    axes[1].axvline(best_count, color="red", linestyle="--",
                    label=f"Выбрано: {best_count}")
    axes[1].set_title("Силуэтный метод")
    axes[1].set_xlabel("Количество кластеров")
    axes[1].set_ylabel("Коэффициент силуэта")
    axes[1].legend()
    fig.tight_layout()

    # 2
    print("\n2. Применение алгоритмов кластеризации")
    kmeans_labels = KMeans(n_clusters=best_count, random_state=42,
                           n_init=10).fit_predict(scaled)
    hierarchy_labels = AgglomerativeClustering(
        n_clusters=best_count, linkage="ward"
    ).fit_predict(scaled)
    dbscan_labels = DBSCAN(eps=0.5, min_samples=5).fit_predict(scaled)
    results = [
        ("K-means", kmeans_labels),
        ("Иерархическая кластеризация", hierarchy_labels),
        ("DBSCAN", dbscan_labels),
    ]
    for name, labels in results:
        print(f"\n{name}:")
        sizes = pd.Series(labels).value_counts().sort_index()
        for cluster, size in sizes.items():
            title = "шум" if cluster == -1 else f"кластер {cluster}"
            print(f"  {title}: {size} клиентов")
        print("  Состав по полу:")
        gender_table = pd.crosstab(pd.Series(labels, name="Кластер"),
                                   df["Gender"])
        print(gender_table.to_string())
        if name == "K-means" and (gender_table.gt(0).sum(axis=1) == 1).all():
            print("  В этом результате кластеры полностью разделились по полу.")
        if name == "DBSCAN":
            print("  Шумовых точек:", int((labels == -1).sum()))

    # 3
    print("\n3. Сравнение метрик кластеризации")
    for name, labels in results:
        print_metrics(name, scaled, labels, exclude_noise=(name == "DBSCAN"))
    print("Для силуэта больше — лучше; для индекса Дэвиса — Болдина меньше — лучше.")
    print("Метрики DBSCAN посчитаны без шума, поэтому они относятся к меньшему набору клиентов.")

    # 4
    print("\n4. Визуализация кластеров в 2D и 3D")
    for name, labels in results:
        show_clusters(df, labels, name)
        print(f"Построены графики: {name}.")
    print("Графики показывают проекции; алгоритмы использовали четыре признака.")
    if plt.get_backend().lower() != "agg":
        plt.show()

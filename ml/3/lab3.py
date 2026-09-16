import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("AirQualityUCI.csv", sep=";", decimal=",", na_values=["-200"])
df = df.drop(columns=["Unnamed: 15", "Unnamed: 16"])
df = df.dropna(how="all")

df["hour"] = df["Time"].str[:2].astype(int)
df["day_part"] = pd.cut(
    df["hour"],
    bins=[-1, 5, 11, 17, 23],
    labels=["ночь", "утро", "день", "вечер"]
)

# 1
print("\n1.")
co_groups = pd.cut(df["CO(GT)"].dropna(), bins=8)
co_counts = co_groups.value_counts().sort_index()
print(co_counts)

plt.figure(figsize=(10, 5))
co_counts.plot(kind="bar", color="skyblue", edgecolor="black")
plt.title("Распределение CO(GT) по интервалам")
plt.xlabel("CO(GT), мг/м3")
plt.ylabel("Количество наблюдений")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.show()

# 2
print("\n2.")
plt.figure(figsize=(10, 5))
co_counts.plot(kind="bar", color="lightgreen", edgecolor="black", logy=True)
plt.title("Распределение CO(GT) по интервалам, логарифмическая шкала")
plt.xlabel("CO(GT), мг/м3")
plt.ylabel("Количество наблюдений, log")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.show()

# 3
print("\n3.")
mean_co = df["CO(GT)"].mean()
t_high_co = df.loc[df["CO(GT)"] > mean_co, "T"].dropna()
t_low_co = df.loc[df["CO(GT)"] <= mean_co, "T"].dropna()
print(f"Средний CO(GT): {mean_co:.2f}")
print(f"Температур при CO выше среднего: {len(t_high_co)}")
print(f"Температур при CO ниже среднего: {len(t_low_co)}")

plt.figure(figsize=(9, 5))
plt.hist(t_high_co, bins=20, color="red", alpha=0.5)
plt.hist(t_low_co, bins=20, color="blue", alpha=0.5)
plt.title("Температура при CO выше и ниже среднего")
plt.xlabel("Температура (°C)")
plt.ylabel("Частота")
plt.legend(["CO выше среднего", "CO ниже среднего"])
plt.tight_layout()
plt.show()

# 4
print("\n4.")
plt.figure(figsize=(9, 5))
plt.hist(t_high_co, bins=20, density=True, color="red", alpha=0.5)
plt.hist(t_low_co, bins=20, density=True, color="blue", alpha=0.5)
plt.title("Плотность распределения температуры")
plt.xlabel("Температура (°C)")
plt.ylabel("Плотность")
plt.legend(["CO выше среднего", "CO ниже среднего"])
plt.tight_layout()
plt.show()

# 5
print("\n5.")
print("Легенда: CO выше среднего - красный, CO ниже среднего - синий")

plt.figure(figsize=(9, 5))
plt.hist(t_high_co, bins=20, density=True, color="red", alpha=0.5,
         label="CO выше среднего")
plt.hist(t_low_co, bins=20, density=True, color="blue", alpha=0.5,
         label="CO ниже среднего")
plt.title("Температура при разном уровне CO(GT)")
plt.xlabel("Температура (°C)")
plt.ylabel("Плотность")
plt.legend()
plt.tight_layout()
plt.show()

# 6
print("\n6.")
benz_by_day_part = df.groupby("day_part", observed=False)["C6H6(GT)"].mean()
print("Средний C6H6(GT) по времени суток:")
print(benz_by_day_part.round(2))

plt.figure(figsize=(8, 5))
benz_by_day_part.plot(kind="bar", color="orange", edgecolor="black")
plt.title("Средний уровень C6H6(GT) по времени суток")
plt.xlabel("Время суток")
plt.ylabel("C6H6(GT), мкг/м3")
plt.xticks(rotation=0)
plt.tight_layout()
plt.show()

# 7
print("\n7.")
co_by_day_part = [
    df.loc[df["day_part"] == "ночь", "CO(GT)"].dropna(),
    df.loc[df["day_part"] == "утро", "CO(GT)"].dropna(),
    df.loc[df["day_part"] == "день", "CO(GT)"].dropna(),
    df.loc[df["day_part"] == "вечер", "CO(GT)"].dropna()
]
print("Количество значений CO(GT) по времени суток:")
for name, values in zip(["ночь", "утро", "день", "вечер"], co_by_day_part):
    print(name, len(values))

plt.figure(figsize=(8, 5))
plt.boxplot(co_by_day_part, tick_labels=["ночь", "утро", "день", "вечер"])
plt.title("CO(GT) по времени суток")
plt.xlabel("Время суток")
plt.ylabel("CO(GT), мг/м3")
plt.tight_layout()
plt.show()

# 8
print("\n8.")
pollutants = ["CO(GT)", "C6H6(GT)", "NOx(GT)"]
colors = ["red", "orange", "green"]
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

for ax, pollutant, color in zip(axes, pollutants, colors):
    data = df[["T", pollutant]].dropna()
    print(f"{pollutant}: {len(data)} точек")
    ax.scatter(data["T"], data[pollutant], color=color, alpha=0.3, s=10)
    ax.set_title(f"{pollutant} и температура")
    ax.set_xlabel("Температура (°C)")
    ax.set_ylabel(pollutant)

plt.tight_layout()
plt.show()

# 9*
print("\n9*.")
area_data = df[["CO(GT)", "C6H6(GT)", "NOx(GT)"]].copy()
area_data = area_data.fillna(area_data.mean())
area_data = area_data.iloc[:200]
print("Первые 200 наблюдений для area plot:")
print(area_data.head())

plt.figure(figsize=(12, 5))
plt.stackplot(
    area_data.index,
    area_data["CO(GT)"],
    area_data["C6H6(GT)"],
    area_data["NOx(GT)"],
    labels=["CO(GT)", "C6H6(GT)", "NOx(GT)"],
    alpha=0.7
)
plt.title("Изменение загрязнителей во времени")
plt.xlabel("Номер наблюдения")
plt.ylabel("Уровень загрязнения")
plt.legend(loc="upper left")
plt.tight_layout()
plt.show()

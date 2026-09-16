import pandas as pd

df = pd.read_csv("AirQualityUCI.csv", sep=";", decimal=",", na_values=["-200"])
df = df.drop(columns=["Unnamed: 15", "Unnamed: 16"])
df = df.dropna(how="all")

# 1
print("\n1.")
print("Данные загружены из файла AirQualityUCI.csv")

# 2
print("\n2.")
print("Первые 5 строк:")
print(df.head())
print("Последние 5 строк:")
print(df.tail())

# 3
print("\n3.")
print(f"Размер: {df.shape[0]} строк x {df.shape[1]} столбцов")

# 4
print("\n4.")
print(list(df.columns))

# 5
print("\n5.")
print(df.isnull().sum())

# 6
print("\n6.")
print(df.describe().round(2))

# 7
print("\n7.")
df.info()
print("\nТипы данных (df.dtypes):")
print(df.dtypes)
print("\nПамять по столбцам (df.memory_usage()):")
print(df.memory_usage())

# 8
print("\n8.")
print(f"Количество уникальных значений: {df['T'].nunique()}")
print("Уникальные значения (все):")
print([float(v) for v in sorted(df["T"].dropna().unique())])
print("Частота встречаемости (топ-10):")
print(df["T"].value_counts().head(10))

# 9
print("\n9.")
filtered9 = df.query("`CO(GT)` > 3 and `T` < 20")
print(f"Количество строк: {len(filtered9)}")
print(filtered9)

# 10
print("\n10.")
df["NOx_CO_ratio"] = df["NOx(GT)"] / df["CO(GT)"]
print(df[["NOx(GT)", "CO(GT)", "NOx_CO_ratio"]].head(10))

# 11
print("\n11.")
print(f"Размер: {df.shape[0]} строк x {df.shape[1]} столбцов")

# 12
print("\n12.")
print(f"Самая частая температура: {df['T'].value_counts().idxmax()} °C, "
      f"встречается {df['T'].value_counts().max()} раз")

# 13
print("\n13.")
missing_benz = df.query("`C6H6(GT)` != `C6H6(GT)`")
print(f"Количество строк без данных о бензоле: {len(missing_benz)}")
if not missing_benz.empty:
    print(missing_benz)

# 14
print("\n14.")
filtered14 = df.loc[df["T"] > 25]
print(f"Измерений при T > 25: {len(filtered14)}")
print("Первые и последние 5 строк:")
print(pd.concat([filtered14.head(5), filtered14.tail(5)]))
print(f"Минимальный CO(GT) при T > 25: {filtered14['CO(GT)'].min():.2f}")

# 15
print("\n15.")
filtered15 = df.loc[df["RH"] > 90]
print(f"Количество измерений с RH > 90%: {len(filtered15)}")
if not filtered15.empty:
    print(filtered15)

# 16
print("\n16.")
mean_above = df.loc[df["T"] > 20, "CO(GT)"].mean()
mean_below = df.loc[df["T"] < 20, "CO(GT)"].mean()
print(f"Средний CO(GT) при T > 20: {mean_above:.2f}")
print(f"Средний CO(GT) при T < 20: {mean_below:.2f}")
print(f"Разница: {mean_above - mean_below:.2f}")

# 17
print("\n17.")
df["High_Ozone"] = (df["PT08.S5(O3)"] > df["PT08.S5(O3)"].mean()).astype(int)
print(df[["PT08.S5(O3)", "High_Ozone"]].head(10))
print(df["High_Ozone"].value_counts())

# 18
print("\n18.")
print(f"Значение: {df['NOx(GT)'].value_counts().idxmax()} "
      f"({df['NOx(GT)'].value_counts().max()} раз)")

# 19
print("\n19.")
mean_benz = df["C6H6(GT)"].mean()
mean_nox = df["NOx(GT)"].mean()
mask19 = (df["C6H6(GT)"] > mean_benz) & (df["NOx(GT)"] > mean_nox)
print(f"Количество измерений: {mask19.sum()}")

# 20
print("\n20.")
mask20 = df["NO2(GT)"] < 50
print(f"Максимальная температура: {df.loc[mask20, 'T'].max():.2f} °C")

# 21
print("\n21.")
mean_co = df["CO(GT)"].mean()
filtered21 = df.query("`CO(GT)` > @mean_co")
print(f"Количество измерений с CO(GT) выше среднего: {len(filtered21)}")
print("Первые 5 строк:")
print(filtered21.head(5))

# 22
print("\n22.")
mean_t = df["T"].mean()
df["temp_group"] = df["T"].apply(
    lambda t: "выше средней" if t > mean_t else "ниже средней")
print(f"Средняя температура: {mean_t:.2f} °C")
print(df["temp_group"].value_counts())
print("Средний C6H6(GT) по группам:")
above_mean = df.query("`temp_group` == 'выше средней'")["C6H6(GT)"].mean()
below_mean = df.query("`temp_group` == 'ниже средней'")["C6H6(GT)"].mean()
print(f"выше средней: {above_mean:.2f}")
print(f"ниже средней: {below_mean:.2f}")
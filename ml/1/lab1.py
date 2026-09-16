import numpy as np

# 1
print("\n1.")
a = np.zeros(10)
print(a)

# 2
print("\n2.")
a = np.zeros(10)
a[4] = 1
print(a)

# 3
print("\n3.")
a = np.random.random(20)
print(a)
print("Индексы ненулевых:", np.nonzero(a)[0])

# 4
print("\n4.")
a = np.random.random((3, 3, 3))
print(a)

# 5
print("\n5.")
a = np.random.random(10)
print(a)
print("Среднее:", np.mean(a))

# 6
print("\n6.")
a = np.random.randint(1, 10, (5, 3))
b = np.random.randint(1, 10, (3, 2))
print(f"A:\n{a}\nB:\n{b}\nA @ B:\n{a @ b}")

# 7
print("\n7.")
a = np.random.randint(1, 10, (4, 4))
b = np.random.randint(1, 10, (4, 4))
c = a @ b
print(f"A:\n{a}\nB:\n{b}\nA @ B:\n{c}\nДиагональ:", np.diag(c))

# 8
print("\n8.")
a = np.random.randint(1, 100, 20)
a[np.argmax(a)] = 0
print(a)

# 9
print("\n9.")
a = np.random.randint(1, 10, 20)
print(a)
print("Без повторений:", np.unique(a))

# 10
print("\n10.")
a = np.random.randint(1, 10, (4, 4)).astype(float)
print(a - a.mean(axis=1, keepdims=True))

# 11
print("\n11.")
a = np.random.randint(1, 10, (4, 4))
print("До:\n", a)
a[[1, 2]] = a[[2, 1]]
print("После:\n", a)

# 12
print("\n12.")
a = np.random.randint(1, 100, 20)
print(a)
n = int(input("n = "))
idx = np.argsort(a)[-n:][::-1]
print(f"{n} наибольших: {a[idx]}\nИндексы: {idx}")

# 13
print("\n13.")
a = np.random.randint(1, 11, (5, 5))
print(a)
print("Суммы строк:", a.sum(axis=1))

# 14
print("\n14.")
a = np.random.uniform(-1, 1, 10)
print(a)
print(np.sign(a))

# 15
print("\n15.")
a = np.random.randint(1, 101, 12)
print(a)
for p in np.array_split(a, 3):
    print(p, "→", np.sum(p))

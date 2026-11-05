import csv,itertools
names=[['Бег','Велосипед','Ходьба'],['Дистанция > 5 км','Время > 30 мин','Сожжено > 300 кал'],['Push','SMS','Email'],['Однократно','Каждый день','Только в выходные']]
rows=[]
for a,b in itertools.product(range(3),repeat=2): rows.append((a,b,(a+b)%3,(a+2*b)%3))
with open('test/4/pairwise.csv','w') as f:
 w=csv.writer(f);w.writerow(['№','Активность','Условие','Канал','Повтор'])
 for i,row in enumerate(rows,1):w.writerow([i]+[names[j][v] for j,v in enumerate(row)])
for i,j in itertools.combinations(range(4),2):
 pairs={(r[i],r[j]) for r in rows};assert len(pairs)==9
print('9 сценариев, 6 пар параметров × 9 сочетаний = 54/54 покрыты')

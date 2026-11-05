from triangle import kind
cases = [(['3','3','3'],'Равносторонний'),(['3','3','4'],'Равнобедренный'),(['3','4','5'],'Разносторонний'),(['1','2','3'],'Не треугольник'),(['0','2','2'],'Не треугольник'),(['-1','2','2'],'Не треугольник'),(['0.0001','0.00015','0.0002'],'Разносторонний'),(['NaN','2','2'],'Не треугольник')]
for values, expected in cases:
    actual = kind(values)
    print(','.join(values), actual, 'PASS' if actual == expected else 'FAIL')
    assert actual == expected

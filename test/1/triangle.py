from decimal import Decimal, InvalidOperation
import sys

def kind(values):
    try:
        a, b, c = (Decimal(x) for x in values)
    except (InvalidOperation, ValueError):
        return 'Ошибка ввода'
    if any(not x.is_finite() or x <= 0 for x in (a, b, c)):
        return 'Не треугольник'
    a, b, c = sorted((a, b, c))
    if a + b <= c:
        return 'Не треугольник'
    if a == c:
        return 'Равносторонний'
    if a == b or b == c:
        return 'Равнобедренный'
    return 'Разносторонний'

if __name__ == '__main__':
    print(kind(sys.argv[1:4]) if len(sys.argv) == 4 else 'Укажите три стороны')

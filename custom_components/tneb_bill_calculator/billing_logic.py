def calculate_bill(units):
    total = 0
    if units <= 500:
        if units > 400:
            total += (units - 400) * 6.30
            units = 400
        if units > 200:
            total += (units - 200) * 4.70
            units = 200
        if units > 100:
            total += (units - 100) * 2.35
            units = 100
        if units > 0:
            total += units * 0.00
        return round(total, 2)

    if units > 1000:
        total += (units - 1000) * 11.55
        units = 1000
    if units > 800:
        total += (units - 800) * 10.50
        units = 800
    if units > 600:
        total += (units - 600) * 9.45
        units = 600
    if units > 500:
        total += (units - 500) * 8.40
        units = 500
    if units > 400:
        total += (units - 400) * 6.30
        units = 400
    if units > 100:
        total += (units - 100) * 4.70
        units = 100
    if units > 0:
        total += units * 0.00
    return round(total, 2)

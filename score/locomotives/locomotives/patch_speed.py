from locomotives.models import Line
lines = Line.objects.all()

for line in lines:
    max_speed = []
    for curve in line.curvature:
        if curve <= 2.0:
            speed = 60
        elif curve <= 3.0:
            speed = 55
        elif curve <= 4.0:
            speed = 50
        elif curve <= 5.0:
            speed = 45
        elif curve <= 6.0:
            speed = 40
        elif curve <= 8.0:
            speed = 35
        elif curve <= 9.0:
            speed = 30
        elif curve <= 10.0:
            speed = 25
        else:
            speed = 20
        max_speed.append(speed)
    print(line.fra_id, max_speed)
    line.max_speed = max_speed
    line.save()
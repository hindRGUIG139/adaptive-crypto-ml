import psutil

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)
def get_battery_level():
    battery=psutil.sensors_battery()
    if battery is None:
        return "No battery detected"
    return battery.percent



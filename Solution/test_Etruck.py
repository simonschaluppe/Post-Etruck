
from post_model import Etruck

def test_workday_schedule():
    daytruck = Etruck()
    assert(daytruck.status(hour_of_day=0, day_of_week=5)=="onsite")
    assert(daytruck.status(hour_of_day=0, day_of_week=6)=="onsite")
    assert(daytruck.status(hour_of_day=0, day_of_week=2)=="offsite")
    assert(daytruck.status(hour_of_day=2, day_of_week=2)=="onsite")
    assert(daytruck.status(hour_of_day=5, day_of_week=2)=="onsite")
    assert(daytruck.status(hour_of_day=7, day_of_week=2)=="offsite")

def test_worknight_schedule():
    truck = Etruck(schedule="worknight")
    assert(truck.status(hour_of_day=0, day_of_week=5)=="onsite")
    assert(truck.status(hour_of_day=0, day_of_week=6)=="onsite")
    assert(truck.status(hour_of_day=0, day_of_week=2)=="offsite")
    assert(truck.status(hour_of_day=4, day_of_week=2)=="offsite")
    assert(truck.status(hour_of_day=11, day_of_week=2)=="onsite")
    assert(truck.status(hour_of_day=19, day_of_week=2)=="offsite")
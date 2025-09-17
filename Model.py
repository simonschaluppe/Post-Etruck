import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

class Battery:
    """a simple battery class with the following default parameters:
    capacity_kWh= 1000
    charge_kW   = 200
    discharge_kW= 200
    current_kWh = capacity_kWh
    """
    capacity_kWh= 1000
    charge_kW   = 200
    discharge_kW= 200
    current_kWh = 0

    @property
    def SoC(self):
        """returns the State of Charge als Wert zwischen [0 - 1]"""
        return self.current_kWh/self.capacity_kWh 

    @property
    def max_charge(self):
        """returns the maximum possible charge to the battery 
        limited by the maximum charging power and the current battery charge 
        for a given hour in [kWh]"""
        return min(self.charge_kW, self.capacity_kWh-self.current_kWh)
    
    @property
    def max_discharge(self):
        """returns the maximum possible DIScharge FROM the battery 
        limited by the maximum DIScharging power and the current battery charge 
        for a given hour in [kWh]"""
        return min(self.discharge_kW, self.current_kWh)

    def charge(self, amount):
        """charges the battery by the maximum possible amount, 
        up to the requested parameter [amount] 
        and RETURNS the actual amount charged (which is <= the [amount] requested)"""
        actual = min(amount, self.max_charge)
        self.current_kWh += actual
        return actual

    def discharge(self, amount):
        """DIScharges the battery by the maximum possible amount, 
        up to the requested parameter [amount] 
        and RETURNS the actual amount charged (which is <= the [amount] requested)"""
        actual = min(amount, self.max_discharge)
        self.current_kWh -= actual
        return actual
    
class Etruck(Battery):
    """represents an Etruck,
    inheriting all Properties of the Battery:
    capacity_kWh = 400     
    charge_kW = 100
    discharge_kW = 150
    consumption = 0.85 # kWh/km
    """
    capacity_kWh = 400     
    charge_kW = 100
    discharge_kW = 150
    consumption = 0.85 # kWh/km

    def __init__(self, 
                 schedule = None, #workday, worknight
                 avg_km_per_h = 15,
                 wd_schedule=None,
                 we_schedule=None,
                 weekly_schedule=None,
                 SoC_minimum=0,
                 ):
        """initializes a truck with a schedule string, and an avg_km_per_h mileage when the schedule is 'offsite'"""
        
        self.schedule = schedule
        self.avg_km_per_h = avg_km_per_h
        self.SoC_minimum = SoC_minimum
        self.current_kWh = self.capacity_kWh

        if weekly_schedule:
            self.weekly_schedule=weekly_schedule
        elif wd_schedule and we_schedule:
            self.weekly_schedule=self.create_weekly_schedule(wd_schedule, we_schedule)
        elif schedule is not None:
            if schedule == "workday":
                self.weekly_schedule=self.create_weekly_schedule(
                    wd_schedule=[0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
                    we_schedule=[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
                )
            elif schedule == "worknight":
                self.weekly_schedule=self.create_weekly_schedule(
                    wd_schedule=[0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0],
                    we_schedule=[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
                )
            elif schedule == "workday_lunchbreak":
                self.weekly_schedule=self.create_weekly_schedule(
                    wd_schedule=[0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0],
                    we_schedule=[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
                )
            elif schedule == "worknight_opt":
                self.weekly_schedule=self.create_weekly_schedule(
                    wd_schedule=[0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0],
                    we_schedule=[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
                )
            else: raise AttributeError(f"Unknown schedule: '{schedule}'")
        else:
            raise AttributeError("Could not create Schedule from variable")

    def create_weekly_schedule(self, wd_schedule, we_schedule):
        schedule = [wd_schedule for _ in range(5)]
        schedule.append(we_schedule)
        schedule.append(we_schedule)
        return schedule 

    def is_chargeable(self, hour_of_day, day_of_week):
        """returns True if the Truck is currently chargeable"""
        return self.weekly_schedule[day_of_week][hour_of_day]
    
    def status(self, hour_of_day, day_of_week):
        boo = self.weekly_schedule[day_of_week][hour_of_day] 
        if boo:
            return "onsite"
        else: return "offsite"

    @property
    def hourly_demand(self):
        """returns the hourly energy demand in [kWh] of a typical hour"""
        return self.avg_km_per_h * self.consumption
    
    @property
    def weekly_energy_demand(self):
        """returns the WEEKLy energy demand in [kWh] of the car"""
        hd = self.hourly_demand
        wd = 0
        for d in range(7):
            for h in range(24):
                if not self.is_chargeable(h,d):
                    wd += hd
        return wd

    def __repr__(self):
        """should return the string:
        Etruck(schedule='schedulestring')
        """
        return(f"Etruck(weekly demand: {self.weekly_energy_demand})")


class Result:
    energy_balance: pd.DataFrame
    states: pd.DataFrame
    pv_kWp: float
    pv_cost_pkWp = 1500
    battery_kWh: float
    battery_cost_pkWh= 300
    grid_tarif_cpkWh = 50
    grid_feedin_cpkWh = 7.06
    co2_intensity = 0.270 #kg/kWh grid
    trucks: list

    def __init__(self, 
        energy_balance=pd.DataFrame(), 
        states=pd.DataFrame(), 
        trucks=None,
        battery_kWh=0,
        pv_kWp=0):
        self.energy_balance = energy_balance
        self.states = states
        self.trucks = trucks if trucks is not None else []

        self.battery_kWh = battery_kWh
        self.states["Battery MAX"] = battery_kWh
        self.states["Fleet MAX"] = self.fleet_capacity_max
        self.states["Fleet MIN"] = self.fleet_capacity_min
        self.pv_kWp = pv_kWp

    @property
    def system_cost(self):
        return self.pv_cost_pkWp*self.pv_kWp + self.battery_cost_pkWh*self.battery_kWh
    
    @property
    def operating_cost(self):
        cost_in_cents = self.energy_balance["Grid to Truck"].sum()*self.grid_tarif_cpkWh - self.energy_balance["PV to Grid"].sum()*self.grid_feedin_cpkWh
        return cost_in_cents / 100
    
    @property
    def emissions(self):
        return self.energy_balance["Grid to Truck"].sum()*self.co2_intensity
    
    @property
    def self_consumption(self):
        return 1-(self.energy_balance["PV to Grid"].sum()/self.states["PV Yield"].sum())
    
    @property
    def fleet_capacity_max(self):
        if len(self.trucks) != 0: 
            return sum(truck.capacity_kWh for truck in self.trucks)
        else: return 0
    
    @property
    def fleet_capacity_min(self):
        return 0
      
    @property
    def load_cycles(self):
        return self.energy_balance["PV to Battery"].sum() / self.battery_kWh
    
    
    def visualize(self, resample=(None, None)):
        states, energy_balance = self.states, self.energy_balance.drop(["Driven"], axis=1)
        if resample[0] is not None:
            states = states.resample(resample[0]).mean()
        if resample[1] is not None:
            energy_balance = energy_balance.resample(resample[1]).sum()
        
        truck_charging = energy_balance[["Grid to Truck",
                                        "PV to Truck",
                                        "Battery to Truck"]
                                        ].resample("M").sum()

        fig, ax = plt.subplots(2,2, figsize=(12,8))
        states.plot(ax=ax[0,0])
        energy_balance.plot(ax=ax[0,1], )
        truck_charging.plot(ax=ax[1,0], stacked=True, kind="barh")
        #TODO: carpet plot: trucks chargin, discharging
        

    def __repr__(self):
        string = f"Energy Flows: \n{self.energy_balance.sum().round()}"
        string += f'\nPV Yield: {self.states["PV Yield"].sum().round():.0f} kWh/a'
        string += "\n" + "_"*20 
        string += f'\nTotal cost: {self.system_cost+self.operating_cost*10:_.0f} €/10a'
        string += f"\n{self.system_cost=:_.1f}€"
        string += f'\n{self.operating_cost=:_.1f}€/a'
        string += f'\n{self.emissions=:.1f}kg/a'
        string += "\n" + "_"*20 
        string += f"\nSelf-consumption: {self.self_consumption*100:.0f}%"
        string += f"\nLoad Cycles: {self.load_cycles:.1f}"
        return string

def monthly_offsite_hours(datetime_index, fleet):
    hours = [0,0,0,0,0,0,0,0,0,0,0,0]
    for i in datetime_index:#
        hd = i.hour
        wd = i.weekday()
        m = i.month
        for truck in fleet:
            hours[m-1] += 1-truck.is_chargeable(hd, wd)
    return hours

def simulate(
        start_day = 0, 
        hours=8760, 
        trucks = [Etruck(schedule="workday")],
        pv_kWp = 200,
        battery_kWh = 2000,
        grid_threshold = 0.2,
        monthly_km = None,
        ):
    
    for truck in trucks:
        truck.SoC_minimum = grid_threshold

    start_hour = start_day * 24
    stop_hour = start_hour + hours
    pv_raw = pv_kWp*np.genfromtxt("data/PV_1kWp.csv")/1000 # -> Wh > kWh/h
    pv = pv_raw[start_hour:stop_hour]

    dt_range = np.arange(start=0, stop=8760, dtype="datetime64[h]")
    energy_balance = pd.DataFrame()
    energy_balance.index = dt_range[start_hour:stop_hour]
    states = pd.DataFrame()
    states.index = dt_range[start_hour:stop_hour]
    
    if monthly_km:
        hours_list = monthly_offsite_hours(
            datetime_index=energy_balance.index,
            fleet=trucks
            )
        truck_km_per_h_per_month = [mkm/h for mkm, h in zip(monthly_km, hours_list)]
        day = [31,28,31,30,31,30,31,31,30,31,30,31]
        days = [[d]*d for d in day]
        daily_km_per_month = [mkm/d for mkm, d in zip(monthly_km, day)]
    else:
        avg_all_trucks = np.array([t.avg_km_per_h for t in trucks]).mean()
        truck_km_per_h_per_month = [avg_all_trucks]*12

    battery = Battery()
    battery.capacity_kWh = battery_kWh
    battery.current_kWh = 0

    current_kWh = np.zeros(hours)
    current_kWh[0] = sum(truck.current_kWh for truck in trucks)
    battery_SOC_kWh = np.zeros(hours)

    gridcharge_kWh = np.zeros(hours)    #Grid > truck
    pvcharge_kWh = np.zeros(hours)      #PV > Truck
    battery_to_truck_kWh = np.zeros(hours) # battery > Truck
    pv_to_battery_kWh = np.zeros(hours)
    pv_to_grid_kWh = np.zeros(hours)
    driven_kWh = np.zeros(hours)

    for h in range(hours):
        i = energy_balance.index[h]
        hd = i.hour
        wd = i.weekday()
        m = i.month

        dispatchable_PV = pv[h]

        for truck in trucks:
        # classic way of doing it, requires all the np arrays
            if truck.is_chargeable(hd, wd):
                pv_used_in_truck = truck.charge(dispatchable_PV)
                pvcharge_kWh[h] += pv_used_in_truck
                dispatchable_PV -= pv_used_in_truck

                batt_used_in_truck = truck.charge(battery.max_discharge)
                battery.discharge(batt_used_in_truck)
                battery_SOC_kWh[h] -= batt_used_in_truck
                battery_to_truck_kWh[h] += batt_used_in_truck
                
                if truck.SoC < truck.SoC_minimum:
                    difference_kWh = (grid_threshold - truck.SoC)*truck.capacity_kWh
                    gridcharge_kWh[h] += truck.charge(difference_kWh)
            
            else:
                driven_kWh[h] += truck.discharge(truck_km_per_h_per_month[m-1]*truck.consumption)/truck.consumption
            current_kWh[h] += truck.current_kWh
        # new dispatch should have all trucks on hold
        # daily_dispatch = daily_km_per_month
        # if no pv > dispatch truck for an hour
        #   
        # if pv > load
        #   dispatch truck(km)


        pv_to_battery_kWh[h] = battery.charge(dispatchable_PV)
        pv_to_grid_kWh[h] = dispatchable_PV - pv_to_battery_kWh[h]
        battery_SOC_kWh[h] = battery.current_kWh
    
    states["PV Yield"] = pv
    states["Fleet SOC"] = current_kWh
    states["Battery SOC"] = battery_SOC_kWh
    energy_balance["Grid"] = gridcharge_kWh
    energy_balance["PV to Truck"] = pvcharge_kWh
    energy_balance["PV to Battery"] = pv_to_battery_kWh
    energy_balance["PV to Grid"] = pv_to_grid_kWh
    energy_balance["Battery to Truck"] = battery_to_truck_kWh
    energy_balance["Grid to Truck"] = gridcharge_kWh
    energy_balance["Driven"] = -driven_kWh

    results = Result(
        energy_balance = energy_balance,
        states = states,
        battery_kWh = battery_kWh,
        pv_kWp = pv_kWp,
        trucks = trucks)
    results.days = days
    return results


def objective_function_2D(x):
    results = simulate(start_day=0, 
                   hours=8760, 
                   trucks=[Etruck("workday_lunchbreak") for i in range(7)], 
                   battery_kWh=x[1], 
                   pv_kWp=x[0],
                   monthly_km=[68000,61000,66000,
                               63000,65000,64000,
                               64000,62000,60000,
                               68000,65000,68000,],
                   grid_threshold=0.99,
                   )
    return (results.system_cost + results.operating_cost*10)


opt_results = [2193.548387096774, 2178.5714285714284, 2129.032258064516, 2100.0, 2096.7741935483873, 2133.3333333333335, 2064.516129032258, 2000.0, 2000.0, 2193.548387096774, 2166.6666666666665, 2193.548387096774]



if __name__ == "__main__":
    t1 = Etruck(wd_schedule=[1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1],
            we_schedule=[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1])

    t2 = Etruck(weekly_schedule=[
            [1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,0,0,0,0,0,0,1,1,0,0,0,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,0,0,0,0,0,0,1,1,0,0,0,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,0,0,0,0,0,0,1,1,0,0,0,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]]
            )

    trucks = [Etruck("workday_lunchbreak") for i in range(7)]
    #trucks+= [Etruck("worknight") for i in range(2)]
    #trucks+= [t1 for i in range(10)]
    #trucks+= [t2 for i in range(10)]

    results = simulate(start_day=0, 
                       hours=8760, 
                       trucks=trucks, 
                       battery_kWh=300, 
                       pv_kWp=192,
                       monthly_km=[68000,61000,66000,
                                   63000,65000,64000,
                                   64000,62000,60000,
                                   68000,65000,68000,],
                       grid_threshold=0.99,
                       )
    results.visualize(("W", "W"))
    print(results)
    dti = results.energy_balance.index
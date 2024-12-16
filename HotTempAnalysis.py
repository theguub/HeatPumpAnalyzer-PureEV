import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI

# Function Definitions
def calculate_lmtd(delta_t1, delta_t2):
    """
    Calculate the Log-Mean Temperature Difference (LMTD).
    Parameters:
        delta_t1 (float): Temperature difference at one end of the heat exchanger.
        delta_t2 (float): Temperature difference at the other end of the heat exchanger.
    Returns:
        float: The LMTD value.
    """
    if delta_t1 == delta_t2:  # Avoid division by zero
        return delta_t1
    return (delta_t1 - delta_t2) / np.log(delta_t1 / delta_t2)

# List of refrigerants to test
refrigerants = ['R134a', 'R32', 'R744']

# Assumptions
mass_flow_rate = 0.05  # kg/s
compressor_efficiency = 0.70  # Realistic efficiency
T_evap_buffer = 5  # Evaporator buffer (°C)
T_cond_buffer = 5  # Condenser buffer (°C)

# Common parameters
T_ambient_C = 25 # Outside temperature (°C)
T_cabin_C = 20 # Desired cabin temperature (°C)

# Convert temperatures to Kelvin
T_ambient_K = T_ambient_C + 273.15
T_cabin_K = T_cabin_C + 273.15
T_ambient_R = T_ambient_K * 1.8  # Source temperature in Rankine
T_cabin_R = T_cabin_K * 1.8  # Sink temperature in Rankine

# Results placeholders
cops = []
heating_capacities = []


# Iterate through each refrigerant
for refrigerant in refrigerants:
    print(f"\n=== Results for {refrigerant} ===")

    # Evaporator and condenser temperatures
    T_evap_C = T_cabin_C - T_evap_buffer  # Evaporator temperature (K) (buffer below ambient)
    T_cond_C = T_ambient_C + T_cond_buffer  # Condenser temperature (K) (buffer above cabin)

    T_evap_K = T_evap_C + 273.15
    T_cond_K = T_cond_C + 273.15


    # Saturation pressures at evaporator and condenser
    P_evap = PropsSI('P', 'T', T_evap_K, 'Q', 1, refrigerant)  # Saturation pressure at evaporator (Pa)
    P_cond = PropsSI('P', 'T', T_cond_K, 'Q', 1, refrigerant)  # Saturation pressure at condenser (Pa)

    # Refrigerant temperatures from thermodynamic properties
    T_cond_in = PropsSI('T', 'P', P_cond, 'Q', 1, refrigerant)  # Saturated vapor (inlet to condenser)
    T_cond_out = PropsSI('T', 'P', P_cond, 'Q', 0, refrigerant)  # Saturated liquid (outlet from condenser)
    T_evap_in = PropsSI('T', 'P', P_evap, 'Q', 0, refrigerant)  # Saturated liquid (inlet to evaporator)
    T_evap_out = PropsSI('T', 'P', P_evap, 'Q', 1, refrigerant)  # Saturated vapor (outlet from evaporator)


    # 1. Evaporator Outlet (Saturated vapor) - compression
    h1 = PropsSI('H', 'T', T_evap_K, 'Q', 1, refrigerant)  # Enthalpy (J/kg)
    s1 = PropsSI('S', 'T', T_evap_K, 'Q', 1, refrigerant)  # Entropy (J/kg.K)

    # 2. Compressor Outlet (Superheated vapor, non-isentropic compression) - condenser
    h2_isentropic = PropsSI('H', 'P', P_cond, 'S', s1, refrigerant)  # Isentropic enthalpy (J/kg)
    h2 = h1 + (h2_isentropic - h1) / compressor_efficiency  # Actual enthalpy after compression (J/kg)
    T2 = PropsSI('T', 'P', P_cond, 'H', h2, refrigerant)  # Calculate actual temperature at compressor outlet (K)
    s2 = PropsSI('S', 'P', P_cond, 'H', h2, refrigerant)  # Calculate actual entropy at compressor outlet (J/kg.K)

    # 3. Condenser Outlet (Saturated liquid) - expansion
    h3 = PropsSI('H', 'T', T_cond_K, 'Q', 0, refrigerant)  # Enthalpy (J/kg)

    # 4. Expansion Valve Outlet (Isenthalpic process) - evaporator
    h4 = h3  # Enthalpy remains constant through expansion valve (J/kg)

    # Heat Delivered by the Condenser (Q_H)
    Q_H = h2 - h3  # Heat released in condenser (J/kg)

    # Heat absorbed by the evaporator (Q_L)
    Q_L = h1 - h4  # Heat absorbed in evaporator (J/kg)

    # Work Input to the Compressor (W_compressor)
    W_compressor = h2 - h1  # Work done by compressor (J/kg)

    # Calculate required compressor power
    P_compressor = mass_flow_rate * W_compressor  # W
    P_compressor_kW = P_compressor / 1000  # Convert to kW

    # Coefficient of Performance (COP)
    COP_cooling = Q_L / W_compressor

    # Maximum COP (Carnot COP)
    COP_max = T_ambient_R / (T_ambient_R - T_cabin_R)

    # Calculate Pressure Ratio
    pressure_ratio = P_cond / P_evap  # Unitless ratio

    # Calculate Heating Capacity
    heating_capacity_cond = mass_flow_rate * Q_H  # (W or J/s)
    cooling_capacity_evap = mass_flow_rate * Q_L  # Evaporator capacity (W)

    # Calculate Maximum and Required Power Consumption
    P_max = cooling_capacity_evap / COP_max  # Maximum power consumption (W)
    P_actual = cooling_capacity_evap / COP_cooling  # Actual power consumption (W)

    # Compare with required heat transfer
    c_p_air = 1005  # J/kg·K
    air_mass_flow_rate = 0.1  # kg/s
    required_heat_transfer = air_mass_flow_rate * c_p_air * (T_ambient_C - T_cabin_C)  # (W or J/s)

    # Assumed heat transfer coefficients (U values)
    U_condenser = 300  # W/m²·K
    U_evaporator = 500  # W/m²·K

    mass_flow_rate_air = 0.1  # Mass flow rate of air (kg/s)

    # Heat transfer calculations (simplified linear assumption for air heating/cooling)
    # Condenser: Heating air (ambient -> cabin)
    heat_released_condenser = mass_flow_rate_air * c_p_air * (T_ambient_K - T_cabin_K)  # Heat released in condenser (W)
    T_cabin_out = T_cabin_K + heat_released_condenser / (mass_flow_rate_air * c_p_air)  # Cabin air outlet temperature

    # Evaporator: Cooling air (ambient)
    heat_absorbed_evaporator = mass_flow_rate_air * c_p_air * (T_cabin_out - T_ambient_K)  # Heat absorbed in evaporator (W)
    T_ambient_out = T_ambient_K - heat_absorbed_evaporator / (mass_flow_rate_air * c_p_air)  # Ambient air outlet temperature


   # Condenser
    delta_T1_condenser = T_cond_in - T_cabin_out  # From thermodynamic properties
    delta_T2_condenser = T_cond_out - T_cabin_K

    # Evaporator
    delta_T1_evaporator = T_ambient_K - T_evap_out  # From thermodynamic properties
    delta_T2_evaporator = T_ambient_out - T_evap_in

    # Calculate LMTD
    LMTD_condenser = calculate_lmtd(delta_T1_condenser, delta_T2_condenser)
    LMTD_evaporator = calculate_lmtd(delta_T1_evaporator, delta_T2_evaporator)

    # Required heat transfer areas
    A_condenser = heating_capacity_cond / (U_condenser * LMTD_condenser)  # Condenser area (m²)
    A_evaporator = cooling_capacity_evap / (U_evaporator * LMTD_evaporator)  # Evaporator area (m²)

    # Energy consumption rates for driving (kWh/100 km)
    E_drive_hot = 15  # Hot weather
    P_cooling_hot = cooling_capacity_evap / 1000  # kW for heating

    # Conversion factor for distance
    km_to_miles = 0.621371

    # Calculate total energy consumption rates (kWh/100 km)
    E_total_hot = E_drive_hot + (P_cooling_hot / 100)  # Hot weather

    # Calculate ranges (km)
    battery_capacity_kWh = 100
    range_hot_km = (battery_capacity_kWh / E_total_hot) * 100

    # Convert ranges to miles
    range_hot_miles = range_hot_km * km_to_miles


    # Append results
    cops.append(COP_cooling)
    heating_capacities.append(cooling_capacity_evap / 1e3)  # Convert to kW


    print("\n=== Enthalpy and Entropy at Each State ===")
    print(f"Evaporator Outlet Enthalpy (h1): {round(h1 / 1e3, 2)} kJ/kg")
    print(f"Compressor Outlet Enthalpy (h2): {round(h2 / 1e3, 2)} kJ/kg")
    print(f"Condenser Outlet Enthalpy (h3): {round(h3 / 1e3, 2)} kJ/kg")
    print(f"Expansion Valve Outlet Enthalpy (h4): {round(h4 / 1e3, 2)} kJ/kg")
    print(f"Compressor Outlet Entropy (s2): {round(s2 / 1e3, 2)} kJ/kg.K")

    print("\n=== Pressure of the Heat Exchangers ===")
    print(f"\nEvaporator Pressure: {round(P_evap / 1e5, 2)} bar")
    print(f"Condenser Pressure: {round(P_cond / 1e5, 2)} bar")
    print(f"Pressure Ratio: {round(pressure_ratio, 2)}")
    if 2.5 <= pressure_ratio <= 4.5:
        print("Pressure ratio is within a good range for efficient operation.")
    else:
        print("Pressure ratio is outside the ideal range. Consider adjusting condenser or evaporator temperatures.")


    # Display the required sizes
    print("\n=== Required Heat Exchanger Sizes ===")
    # Print the LMTD values
    print(f"LMTD (Condenser): {LMTD_condenser:.2f} K")
    print(f"LMTD (Evaporator): {LMTD_evaporator:.2f} K")

    # Print the heat exchanger areas
    print(f"Condenser Area: {A_condenser:.2f} m²")
    print(f"Evaporator Area: {A_evaporator:.2f} m²")


    # Statements about system requirements
    if A_condenser > 1.5:
        print("The condenser size is large. Ensure adequate space for installation.")
    else:
        print("The condenser size is reasonable for typical applications.")


    if A_evaporator > 1.5:
        print("The evaporator size is large. Consider optimizing the design.")
    else:
        print("The evaporator size is reasonable for typical applications.")


    print("\n=== Coefficient of Performance (COP) ===")
    print(f"Actual COP (Heating): {round(COP_cooling, 2)}")
    print(f"Maximum COP (Carnot): {round(COP_max, 2)}")
    # Verify if the actual COP is realistic and efficient
    if 3.5 <= COP_cooling <= 6 and COP_cooling < COP_max:
        print(f"The actual COP ({round(COP_cooling, 2)}) is within the realistic and efficient range (3.5 to 6) and is less than the maximum COP ({round(COP_max, 2)}).")
    elif COP_cooling>= COP_max:
        print(f"The actual COP ({round(COP_cooling, 2)}) exceeds the maximum COP ({round(COP_max, 2)}), which is unrealistic.")
    else:
        print(f"The actual COP ({round(COP_cooling, 2)}) is outside the realistic and efficient range (3.5 to 6) or invalid.")


    print("\n=== Heating and Power Calculations ===")
    print(f"Heat Delivered (Q_H): {round(Q_H / 1e3, 2)} kJ/kg")
    print(f"Cooling Capacity: {round(cooling_capacity_evap / 1e3, 2)} kW")
    print(f"Required Heat Transfer: {round(required_heat_transfer / 1e3, 2)} kW")
    print(f"Capacity Check: {'Sufficient' if cooling_capacity_evap >= required_heat_transfer else 'Insufficient'}")

    print("\n=== Required Compressor Power ===")
    print(f"Compressor Work: {round(W_compressor / 1e3, 2)} kJ/kg")
    print(f"Compressor Power: {round(P_compressor_kW, 2)} kW")
    print(f"Maximum Power Consumption: {round(P_max / 1e3, 2)} kW")
    print(f"Actual Power Consumption: {round(P_actual / 1e3, 2)} kW")

    print("\n=== Travel Range Estimates ===")
    print(f"Energy Consumption (Hot, kWh/100 km): {round(E_total_hot, 2)}")
    print(f"Range (Hot, km): {round(range_hot_km, 2)} km")
    print(f"Range (Hot, miles): {round(range_hot_miles, 2)} miles")


    # Check if the range is within the average range of 250 to 500 miles
    print("\n=== Range Analysis ===")


    if 250 <= range_hot_miles <= 500:
        print(f"Hot Weather Range ({round(range_hot_miles, 2)} miles): Within the average range of 250 to 500 miles for Pure EVs.")
    else:
        print(f"Hot Weather Range ({round(range_hot_miles, 2)} miles): Outside the average range of 250 to 500 miles for Pure EVs.")


        print("\n=== End of Simulation for All Refrigerants ===")

# Add buffer to y-axis ranges for visual clarity
cop_y_range = [0, max(cops) + 1]  # Buffer above maximum COP
heating_y_range = [0, max(heating_capacities) + 1]  # Buffer above maximum heating capacity


# Plot COPs
plt.figure(figsize=(8, 6))
bars = plt.bar(refrigerants, cops, color='blue', alpha=0.7)
plt.title("COP Comparison for Refrigerants at Warm Temps.", fontsize=14)
plt.xlabel("Refrigerants", fontsize=12)
plt.ylabel("COP", fontsize=12)
plt.ylim(cop_y_range)
plt.grid(axis='y', linestyle='--', alpha=0.7)
# Add COP values above bars
for bar in bars:
    plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
             f"{bar.get_height():.2f}", ha='center', va='bottom', fontsize=10)
plt.show()

# Plot Heating Capacities
plt.figure(figsize=(8, 6))
bars = plt.bar(refrigerants, heating_capacities, color='green', alpha=0.7)
plt.title("Heating Capacity Comparison for Refrigerants at Warm Temps.", fontsize=14)
plt.xlabel("Refrigerants", fontsize=12)
plt.ylabel("Heating Capacity (kW)", fontsize=12)
plt.ylim(heating_y_range)
plt.grid(axis='y', linestyle='--', alpha=0.7)
# Add heating capacity values above bars
for bar in bars:
    plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
             f"{bar.get_height():.2f}", ha='center', va='bottom', fontsize=10)
plt.show()

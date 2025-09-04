"""
Constants for DTSU666 measurement keys
"""

VOLTAGE_PHASE_AB = "Voltage_Phase_AB"
VOLTAGE_PHASE_BC = "Voltage_Phase_BC"
VOLTAGE_PHASE_CA = "Voltage_Phase_CA"
VOLTAGE_PHASE_A  = "Voltage_Phase_A"
VOLTAGE_PHASE_B  = "Voltage_Phase_B"
VOLTAGE_PHASE_C  = "Voltage_Phase_C"

CURRENT_PHASE_A = "Current_Phase_A"
CURRENT_PHASE_B = "Current_Phase_B"
CURRENT_PHASE_C = "Current_Phase_C"

ACTIVE_POWER_PHASE_A = "Active_Power_Phase_A"
ACTIVE_POWER_PHASE_B = "Active_Power_Phase_B"
ACTIVE_POWER_PHASE_C = "Active_Power_Phase_C"

REACTIVE_POWER_PHASE_A = "Reactive_Power_Phase_A"
REACTIVE_POWER_PHASE_B = "Reactive_Power_Phase_B"
REACTIVE_POWER_PHASE_C = "Reactive_Power_Phase_C"

POWER_FACTOR_PHASE_A = "Power_Factor_Phase_A"
POWER_FACTOR_PHASE_B = "Power_Factor_Phase_B"
POWER_FACTOR_PHASE_C = "Power_Factor_Phase_C"

TOTAL_ACTIVE_POWER   = "Total_Active_Power"
TOTAL_REACTIVE_POWER = "Total_Reactive_Power"
TOTAL_POWER_FACTOR   = "Total_Power_Factor"

FREQUENCY = "Frequency"

TOTAL_IMPORT_ENERGY = "Total_Import_Energy"
TOTAL_EXPORT_ENERGY = "Total_Export_Energy"

# Constants for DTSU666 measurement registers

MEASUREMENTS = {
    "Voltage_Phase_AB": {"address": 0x2000, "func": 3, "words": 2, "factor": 0.1},
    "Voltage_Phase_BC": {"address": 0x2002, "func": 3, "words": 2, "factor": 0.1},
    "Voltage_Phase_CA": {"address": 0x2004, "func": 3, "words": 2, "factor": 0.1},
    "Voltage_Phase_A":  {"address": 0x2006, "func": 3, "words": 2, "factor": 0.1},
    "Voltage_Phase_B":  {"address": 0x2008, "func": 3, "words": 2, "factor": 0.1},
    "Voltage_Phase_C":  {"address": 0x200A, "func": 3, "words": 2, "factor": 0.1},

    "Current_Phase_A": {"address": 0x200C, "func": 3, "words": 2, "factor": 0.001},
    "Current_Phase_B": {"address": 0x200E, "func": 3, "words": 2, "factor": 0.001},
    "Current_Phase_C": {"address": 0x2010, "func": 3, "words": 2, "factor": 0.001},

    "Active_Power_Phase_A": {"address": 0x2014, "func": 3, "words": 2, "factor": 0.1},
    "Active_Power_Phase_B": {"address": 0x2016, "func": 3, "words": 2, "factor": 0.1},
    "Active_Power_Phase_C": {"address": 0x2018, "func": 3, "words": 2, "factor": 0.1},

    "Reactive_Power_Phase_A": {"address": 0x201C, "func": 3, "words": 2, "factor": 0.1},
    "Reactive_Power_Phase_B": {"address": 0x201E, "func": 3, "words": 2, "factor": 0.1},
    "Reactive_Power_Phase_C": {"address": 0x2020, "func": 3, "words": 2, "factor": 0.1},

    "Power_Factor_Phase_A": {"address": 0x202C, "func": 3, "words": 2, "factor": 0.001},
    "Power_Factor_Phase_B": {"address": 0x202E, "func": 3, "words": 2, "factor": 0.001},
    "Power_Factor_Phase_C": {"address": 0x2030, "func": 3, "words": 2, "factor": 0.001},

    "Total_Active_Power":   {"address": 0x2012, "func": 3, "words": 2, "factor": 0.1},
    "Total_Reactive_Power": {"address": 0x201A, "func": 3, "words": 2, "factor": 0.1},
    "Total_Power_Factor":   {"address": 0x202A, "func": 3, "words": 2, "factor": 0.001},

    "Frequency": {"address": 0x2044, "func": 3, "words": 2, "factor": 0.01},

    "Total_Import_Energy": {"address": 0x401E, "func": 3, "words": 2, "factor": 1},
    "Total_Export_Energy": {"address": 0x4028, "func": 3, "words": 2, "factor": 1},
}

# Optional: Liste aller Keys, z.B. für Iterationen
ALL_KEYS = [
    VOLTAGE_PHASE_AB,
    VOLTAGE_PHASE_BC,
    VOLTAGE_PHASE_CA,
    VOLTAGE_PHASE_A,
    VOLTAGE_PHASE_B,
    VOLTAGE_PHASE_C,
    CURRENT_PHASE_A,
    CURRENT_PHASE_B,
    CURRENT_PHASE_C,
    ACTIVE_POWER_PHASE_A,
    ACTIVE_POWER_PHASE_B,
    ACTIVE_POWER_PHASE_C,
    REACTIVE_POWER_PHASE_A,
    REACTIVE_POWER_PHASE_B,
    REACTIVE_POWER_PHASE_C,
    POWER_FACTOR_PHASE_A,
    POWER_FACTOR_PHASE_B,
    POWER_FACTOR_PHASE_C,
    TOTAL_ACTIVE_POWER,
    TOTAL_REACTIVE_POWER,
    TOTAL_POWER_FACTOR,
    FREQUENCY,
    TOTAL_IMPORT_ENERGY,
    TOTAL_EXPORT_ENERGY,
]
FOUR_WIRE_KEYS = [
    VOLTAGE_PHASE_A,
    VOLTAGE_PHASE_B,
    VOLTAGE_PHASE_C,
    CURRENT_PHASE_A,
    CURRENT_PHASE_B,
    CURRENT_PHASE_C,
    ACTIVE_POWER_PHASE_A,
    ACTIVE_POWER_PHASE_B,
    ACTIVE_POWER_PHASE_C,
    REACTIVE_POWER_PHASE_A,
    REACTIVE_POWER_PHASE_B,
    REACTIVE_POWER_PHASE_C,
    POWER_FACTOR_PHASE_A,
    POWER_FACTOR_PHASE_B,
    POWER_FACTOR_PHASE_C,
    TOTAL_ACTIVE_POWER,
    TOTAL_REACTIVE_POWER,
    TOTAL_POWER_FACTOR,
    FREQUENCY,
    TOTAL_IMPORT_ENERGY,
    TOTAL_EXPORT_ENERGY,
]

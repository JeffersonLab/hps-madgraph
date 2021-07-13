"""Data with physics run parameters by beam energy."""

import sys

run_params = {
    "aprime_mass": {
        "1pt05": [15, 20, 30, 40, 50, 60, 70, 80, 90],
        "1pt1": [15, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        "1pt92": [50, 75, 100],
        "2pt2": [15, 25, 50, 75, 100, 150, 200, 250],
        "2pt3": [15, 25, 50, 75, 100, 150, 200, 250],
        "3pt7": [15, 25, 50, 75, 100, 150, 200, 250, 300, 350],
        "4pt4": [15, 25, 50, 75, 100, 150, 200, 250, 300, 350, 400, 450, 500],
        "4pt55": [75, 90, 100, 105, 110, 115, 120, 125, 130, 135, 140, 145, 150, 160, 170, 180, 190, 200],
        "6pt6": [50, 100, 200, 300, 400, 500, 600]
    },
    "target_z": {
        "1pt1": 0.0004062,
        "1pt92": 0.0004062,
        "1pt05": 0.0004062,
        "2pt2": 0.0004062,
        "2pt3": 0.0004062,
        "3pt7": 0.002,
        "4pt4": 0.0004062,
        "4pt55": 0.002,
        "6pt6": 0.000875
    },
    "beam_energy": {
        "1pt1": 1100.00,
        "1pt92": 1920.00,
        "1pt05": 1056.00,
        "2pt2": 2200.00,
        "2pt3": 2300.00,
        "3pt7": 3700.00,
        "4pt4": 4400.00,
        "4pt55": 4550.00,
        "6pt6": 6600.00
    },
    "num_electrons": {
        "1pt05": 625,
        "1pt1": 625,
        "1pt92": 2500,
        "2pt2": 2500,
        "2pt3": 2500,
        "3pt7": 1500,
        "4pt4": 5000,
        "4pt55": 1500,
        "6pt6": 5625
    }
}

class RunParameters:

    def __init__(self, key, json_filename = None):
        self.key = key

    def get(self, param_name):
        return run_params[param_name][self.key]

if __name__ == "__main__":

    rp = RunParameters()

    if len(sys.argv) != 3:
        raise Exception("Not enough arguments.\nUSAGE: run_params [param] [key]")

    param_name = sys.argv[1]
    key = sys.argv[2]

    print(rp.get_run_params(param_name, key))

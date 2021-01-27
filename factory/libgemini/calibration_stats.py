# Copyright (c) 2021 Alethea Katherine Flowers.
# Published under the standard MIT License.
# Full text available at: https://opensource.org/licenses/MIT

import argparse
import json
from pathlib import Path
import statistics
import sys

from libwinter import tui
from libgemini.ramp_calibration import _period_reg_to_freq

calibration_files = Path(Path(__file__).parent, "../calibrations").glob("*.ramp.json")
reference_calibration_file = Path(Path(__file__).parent, "reference_calibration.py")


def run(dry_run=False):
    castor_calibration_values = {}
    pollux_calibration_values = {}

    for filepath in calibration_files:
        with filepath.open("r") as fh:
            data = json.load(fh)

        for key, value in data["castor"].items():
            if key not in castor_calibration_values:
                castor_calibration_values[key] = [value]
            else:
                castor_calibration_values[key].append(value)

        for key, value in data["pollux"].items():
            if key not in pollux_calibration_values:
                pollux_calibration_values[key] = [value]
            else:
                pollux_calibration_values[key].append(value)

    # Print out stats for each calibration point
    for period in castor_calibration_values.keys():
        c_average = statistics.mean(castor_calibration_values[period])
        c_stddev = statistics.stdev(castor_calibration_values[period])
        p_average = statistics.mean(pollux_calibration_values[period])
        p_stddev = statistics.stdev(pollux_calibration_values[period])

        c_color = tui.gradient((1.0, 1.0, 1.0), (1.0, 0.0, 0.0), c_stddev / 100)
        p_color = tui.gradient((1.0, 1.0, 1.0), (1.0, 0.0, 0.0), p_stddev / 100)
        print(
            f"Frequency: {_period_reg_to_freq(int(period)):.2f} Hz, period register: {period}:\n"
            f"- Castor: average: {c_average:.0f}, stddev: {tui.rgb(c_color)}{c_stddev:.0f}{tui.reset}\n"
            f"- Pollux: average: {p_average:.0f}, stddev: {tui.rgb(p_color)}{p_stddev:.0f}{tui.reset}\n"
            f"> Difference: {abs(c_average - p_average):.0f}, stddev: {abs(c_stddev - p_stddev):.0f}"
        )

        # Show this data as a bar graph.
        bar = tui.Bar(width=tui.width())
        if c_average < p_average:
            a_segment = tui.Segment(c_average / 4095, color=(1.0, 0.3, 1.0))
            b_segment = tui.Segment(
                (p_average - c_average) / 4095, color=(0.3, 1.0, 1.0)
            )
        else:
            a_segment = tui.Segment(p_average / 4095, color=(0.3, 1.0, 1.0))
            b_segment = tui.Segment(
                (c_average - p_average) / 4095, color=(1.0, 0.3, 1.0)
            )

        bar.draw(sys.stdout, a_segment, b_segment)

    if dry_run:
        print("Dry run, not generating new reference calibration.")
        return

    # Create a new reference calibration.
    print("Generating new reference calibration...")

    with reference_calibration_file.open("w") as fh:
        fh.write("castor = {\n")
        for key, value in castor_calibration_values.items():
            fh.write(f"    {key}: {int(statistics.mean(value))},\n")
        fh.write("}\n\n")
        fh.write("pollux = {\n")
        for key, value in pollux_calibration_values.items():
            fh.write(f"    {key}: {int(statistics.mean(value))},\n")
        fh.write("}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        default=False,
        help="Don't generate a new reference calibration.",
    )

    args = parser.parse_args()

    run(args.dry_run)

import os
from pathlib import Path

import numpy as np

from wavgen import utilities
from wavgen.constants import DATA_MAX, SAMP_FREQ
from wavgen.waveform import Superposition
from wavgen.waveform import Sweep_sequence as _SweepSequence


class Sweep_sequence(_SweepSequence):

    def compute(self, p, q):
        sample_count = min(DATA_MAX, self.SampleLength - p * DATA_MAX)
        start = p * DATA_MAX
        n = np.arange(start, start + sample_count, dtype=np.float64)
        waveform = np.zeros(sample_count, dtype=np.float64)
        duration = float(self.SampleLength)

        for initial, final in zip(self.WavesA, self.WavesB):
            omega_a = 2 * np.pi * initial.Frequency / SAMP_FREQ
            omega_b = 2 * np.pi * final.Frequency / SAMP_FREQ
            phase_a = initial.Phase
            phase_b = final.Phase
            delta_phase = (
                np.pi
                + phase_b
                - phase_a
                - (omega_a + omega_b) * duration / 2
            ) % (2 * np.pi) - np.pi
            acceleration = (omega_b - omega_a) / duration
            phase = (
                phase_a
                + omega_a * n
                + acceleration * n**2 / 2
                + acceleration
                * (duration / (2 * np.pi)) ** 2
                * (np.cos(2 * np.pi * n / duration) - 1)
                + delta_phase
                * (3 * duration - 2 * n)
                * n**2
                / duration**3
            )
            envelope = 1.25 - (n / duration - 0.5) ** 2
            waveform += envelope * np.sin(phase)

        q.put((p, waveform, float(np.max(np.abs(waveform)))))


if __name__ == "__main__":
    ntraps = 26  # Number of wanted tweezers plus one.
    center_freq = 101.44E6
    CenterFreq = 101.44E6
    Lambda = 0.16E6
    spacing_Lambda = 4.5
    spacing = spacing_Lambda * Lambda
    startfreq = CenterFreq - ntraps * spacing / 2

    for sweep_mode in ["cosine"]:
        for sweep_time in [0.24]:
            folder_name = "FourPtFiveLambda-25Tweezers"
            folder = Path(folder_name)
            if not os.path.isdir(folder):
                os.mkdir(folder)
                print("directory created")

            # Right-side sweeps
            for sweep_num in np.arange(ntraps - 2) + 1:
                filename = folder / f"sweep_{sweep_num}R.h5"
                if os.access(filename, os.F_OK):
                    print("file exists")
                    AB = utilities.from_file(filename, "AB")
                else:
                    print("computing new file")
                    phase_diff = (
                        np.arange(ntraps - 1)
                        / (ntraps - 2)
                        * 2
                        * np.pi
                    )
                    phasesB = np.cumsum(phase_diff)
                    freq_A = []
                    phasesA = []

                    startfreq = center_freq - (ntraps - 1) / 2 * spacing
                    f_list = [
                        startfreq + j * spacing for j in range(ntraps)
                    ]
                    for i in range(ntraps):
                        if i < ntraps - 2 - sweep_num:
                            freq_A.append(f_list[i])
                        if i >= ntraps - 1 - sweep_num:
                            freq_A.append(f_list[i])
                    freq_B = f_list[:-1]

                    for i in range(len(phasesB)):
                        if i < len(phasesB) - sweep_num - 1:
                            phasesA.append(phasesB[i])
                        elif i >= len(phasesB) - sweep_num:
                            phasesA.append(phasesB[i])
                    phasesA.append(phasesB[-1])

                    A = Superposition(freq_A, phases=phasesA)
                    B = Superposition(freq_B, phases=phasesB)
                    AB = Sweep_sequence(
                        A,
                        B,
                        sweep_time=sweep_time,
                        ramp=sweep_mode,
                        segment=False,
                    )
                    AB.compute_waveform(filename, "AB")

            # Left-side sweeps.
            for sweep_num in np.arange(ntraps - 2) + 1:
                filename = folder / f"sweep_{sweep_num}.h5"
                if os.access(filename, os.F_OK):
                    print("file exists")
                    AB = utilities.from_file(filename, "AB")
                else:
                    print("computing new file")
                    phase_diff = (
                        np.arange(ntraps - 1)
                        / (ntraps - 2)
                        * 2
                        * np.pi
                    )
                    phasesB = np.cumsum(phase_diff)
                    freq_A = []
                    phasesA = []

                    startfreq = center_freq - (ntraps + 1) / 2 * spacing
                    f_list = [
                        startfreq + j * spacing for j in range(ntraps)
                    ]
                    for i in range(ntraps):
                        if i <= sweep_num:
                            freq_A.append(f_list[i])
                        if i > sweep_num + 1:
                            freq_A.append(f_list[i])

                    for i in range(len(phasesB)):
                        if i == 0:
                            phasesA.append(phasesB[0])
                        elif 0 < i <= sweep_num:
                            phasesA.append(phasesB[i - 1])
                        else:
                            phasesA.append(phasesB[i])
                    freq_B = f_list[1:]

                    A = Superposition(freq_A, phases=phasesA)
                    B = Superposition(freq_B, phases=phasesB)
                    AB = Sweep_sequence(
                        A,
                        B,
                        sweep_time=sweep_time,
                        ramp=sweep_mode,
                        segment=False,
                    )
                    AB.compute_waveform(filename, "AB")

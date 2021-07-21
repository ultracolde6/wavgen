from math import pi, sin, cosh, log
from .waveform_base import Waveform
from .utilities import Wave
from easygui import msgbox
from sys import maxsize
from .constants import *
from math import inf
import numpy as np
import random
from .waveform import Superposition


class Sweep1(Waveform):
    def __init__(self, config_a, config_b, hold_time_a = 100, hold_time_b = 100, sweep_time=None, sample_length=int(250E6)):
        """ Allows for defining the duration in terms of milliseconds or samples.

        Parameters
        ----------
        config_a, config_b : :class:`~wavgen.waveform.Superposition`
            These play the initial & final configurations of the Sweep form,
            going from **A** to **B** respectively.
        sweep_time : float, optional
            The time, in milliseconds, that the waveform will spend to complete
            the entire modulation. **Overrides sample_length**
        sample_length : int, optional
            Otherwise, one can simply fix the length to an integer number of samples.
        """
        assert isinstance(config_a, Superposition) and isinstance(config_b, Superposition)
        assert len(config_a.Waves) == len(config_b.Waves)

        if sweep_time:
            sample_length = int(SAMP_FREQ*(hold_time_a+sweep_time+hold_time_b)/1000)

        self.WavesA = config_a.Waves
        self.WavesB = config_b.Waves
        self.Damp = (config_b.Amplitude / config_a.Amplitude - 1) / sample_length
        self.hold_time_a = hold_time_a
        self.hold_time_b = hold_time_b
        self.sweep_time = sweep_time

        super().__init__(sample_length, max(config_a.Amplitude, config_b.Amplitude))

    def compute(self, p, q):
        N = min(DATA_MAX, self.SampleLength - p * DATA_MAX)
        HoldTimeA = int(self.hold_time_a * self.SampleLength/(self.hold_time_a + self.hold_time_b + self.sweep_time))
        SweepTime = int(self.sweep_time * self.SampleLength / (self.hold_time_a + self.hold_time_b + self.sweep_time))
        waveform = np.empty(N, dtype=float)

        ## For each Pure Tone ##
        for j, (a, b) in enumerate(zip(self.WavesA, self.WavesB)):
            f_a = a.Frequency / SAMP_FREQ  # Cycles/Sample
            f_b = b.Frequency / SAMP_FREQ
            dfn_inc = (b.Frequency - a.Frequency) / (SAMP_FREQ * self.SampleLength)

            phi = a.Phase
            phi_inc = (b.Phase - phi) / self.SampleLength

            mag = a.Magnitude
            mag_inc = (b.Magnitude - mag) / self.SampleLength

            # freq_list = []

            ## Compute the Wave ##
            for i in range(N):
                n = i + p * DATA_MAX
                dfn = dfn_inc * n / 2  # Sweep Frequency shift, ask Aron about the 2
                # print(n)
                # if n < HoldTimeA:
                #     freq_list.append(fn)
                # if HoldTimeA <= n <= HoldTimeA + SweepTime:
                #     freq_list.append(fn + dfn)
                # if n > HoldTimeA + SweepTime:
                #     freq_list.append(b.Frequency / SAMP_FREQ)
                # # print(freq_list[n], n)
                # waveform[i] += (1 + n * self.Damp) * (mag + n * mag_inc) * sin(2 * pi * n * freq_list[n] + (phi + n * phi_inc))
                # waveform[i] += (1 + n * self.Damp) * (mag + n * mag_inc) * sin(2 * pi * n * (fn + dfn) + (phi + n * phi_inc))

                if n < HoldTimeA:
                    waveform[i] += mag * sin(2 * pi * n * f_a + phi)

                if HoldTimeA <= n <= HoldTimeA + SweepTime:
                    waveform[i] += (1 + n * self.Damp) * (mag + n * mag_inc) * sin(2 * pi * n * (f_a + dfn) + (phi + n * phi_inc))
                if n > HoldTimeA + SweepTime:
                    waveform[i] += mag * sin(2 * pi * n * f_b + phi)

        ## Send the results to Parent ##
        q.put((p, waveform, max(waveform.max(), abs(waveform.min()))))

    def config_dset(self, dset):
        ## Contents ##
        dset.attrs.create('freqsA', data=np.array([w.Frequency for w in self.WavesA]))
        dset.attrs.create('magsA', data=np.array([w.Magnitude for w in self.WavesA]))
        dset.attrs.create('phasesA', data=np.array([w.Phase for w in self.WavesA]))

        dset.attrs.create('freqsB', data=np.array([w.Frequency for w in self.WavesB]))
        dset.attrs.create('magsB', data=np.array([w.Magnitude for w in self.WavesB]))
        dset.attrs.create('phasesB', data=np.array([w.Phase for w in self.WavesB]))

        dset.attrs.create('sample_length', data=self.SampleLength)

        ## Table of Contents ##
        dset.attrs.create('keys', data=['freqsA', 'magsA', 'phasesA', 'freqsB', 'magsB', 'phasesB', 'sample_length'])

        return dset

    @classmethod
    def from_file(cls, **kwargs):
        freqsA, magsA, phasesA, freqsB, magsB, phasesB, sample_length = kwargs.values()
        supA = Superposition(freqsA, magsA, phasesA)
        supB = Superposition(freqsB, magsB, phasesB)

        return cls(supA, supB, sample_length=sample_length)


from math import pi, sin, cosh, log
from .waveform_base import Waveform
from .utilities import Wave
from easygui import msgbox
from sys import maxsize
from .constants import *
from math import inf
import numpy as np
import random


class Superposition(Waveform):
    """ A static trap configuration.

    Attributes
    ----------
    Waves : list of :class:`~wavgen.utilities.Wave`
        The list of composing pure tones. Each object holds a frequency,
        magnitude, and relative phase.

    Hint
    ----
    There are now 3 relevant **amplitudes** here:
    :meth:`Output Voltage Limit <wavgen.card.Card.setup_channels>`,
    :attr:`Waveform Amplitude <wavgen.waveform.Waveform.Amplitude>`, & the
    :attr:`amplitudes of each pure tone <wavgen.utilities.Wave.Magnitude>`
    composing a superposition. Each one is expressed as a fraction of the previous.

    See Also
    --------
    :func:`even_spacing`
        An alternative constructor for making :class:`Superposition` objects.
    """
    def __init__(self, freqs, mags=None, phases=None, sample_length=None, amp=1.0):
        """ Provides several options for defining waveform duration.

        Parameters
        ----------
        freqs : list of int
            A list of frequency values, from which wave objects are automatically created.
        mags : list of float, optional
            Vector representing relative magnitude of each trap, within [0,1] (in order of increasing frequency).
        phases : list of float, optional
            Vector representing initial phases of each trap tone, within [0, 2*pi]
            (in order of increasing frequency).
        sample_length : int, optional
            Length of waveform in samples.
        amp : float, optional
            Amplitude of waveform relative to maximum output voltage.
        """
        freqs.sort()

        ## Find the LeastCommonMultiple ##
        if sample_length is None:
            # sample_length = int(SAMP_FREQ * (2 - len(freqs) % 2)//10E6) * 32 * REPEAT *2 # Jacqie made this edit with 10e6 chosen randomly
            # This edit did not work -- intensity jump seen between repetitions due (probably) to phase mis-match. -ED 2021-07-02

            lcm = inf
            for f in freqs:
                digits = 0
                while f%10 == 0:
                    f = f // 10
                    digits += 1
                lcm = min(digits, lcm)
                """
                + 1
                """
            sample_length = (SAMP_FREQ / 10**lcm) * 32 * REPEAT
            msg = "Waveform will not be an integer # of periods.\nYou may want to calculate a sample length manually"
        if sample_length % 1:
            msgbox(msg, "Warning")
        else:
            sample_length = int(sample_length)

        ## Applies passed Magnitudes or Phases ##
        if mags is None:
            mags = np.ones(len(freqs))
        if phases is None:
            phases = np.zeros(len(freqs))

        assert freqs[-1] >= SAMP_FREQ/sample_length, "Frequency is below resolution. Increase sample length."
        assert freqs[0] < SAMP_FREQ / 2, ("Frequency %d must below Nyquist: %d" % (freqs[0], SAMP_FREQ / 2))
        assert len(mags) == len(freqs) == len(phases), "Parameter size mismatch!"

        ## Initialize ##
        self.Waves = [Wave(f, m, p) for f, m, p in zip(freqs, mags, phases)]
        super().__init__(sample_length, amp)

    def compute(self, p, q):
        N = min(DATA_MAX, self.SampleLength - p*DATA_MAX)
        waveform = np.zeros(N, dtype=float)

        ## For each Pure Tone ##
        for j, w in enumerate(self.Waves):
            f = w.Frequency
            phi = w.Phase
            mag = w.Magnitude

            fn = f / SAMP_FREQ  # Cycles/Sample
            ## Compute the Wave ##
            for i in range(N):
                n = i + p*DATA_MAX
                waveform[i] += mag * sin(2 * pi * n * fn + phi)

        ## Send the results to Parent ##
        q.put((p, waveform, max(waveform.max(), abs(waveform.min()))))

    def config_dset(self, dset):
        ## Contents ##
        dset.attrs.create('freqs', data=np.array([w.Frequency for w in self.Waves]))
        dset.attrs.create('mags', data=np.array([w.Magnitude for w in self.Waves]))
        dset.attrs.create('phases', data=np.array([w.Phase for w in self.Waves]))
        dset.attrs.create('sample_length', data=self.SampleLength)

        ## Table of Contents ##
        dset.attrs.create('keys', data=['freqs', 'mags', 'phases', 'sample_length'])

        return dset

    def get_magnitudes(self):
        """
        Returns
        -------
        list of float
            Value of :attr:`~wavgen.utilities.Wave.Magnitude` for each pure tone,
            in order of increasing frequency.
        """
        return [w.Magnitude for w in self.Waves]

    def set_magnitudes(self, mags):
        """ Sets the :attr:`~wavgen.utilities.Wave.Magnitude` of each pure tone.

        Parameters
        ----------
        mags : list of float
            Each new magnitude, limited to (**[0, 1]**), ordered by ascending frequency).
        """
        for w, mag in zip(self.Waves, mags):
            assert 0 <= mag <= 1, ("Invalid magnitude: %d, must be within interval [0,1]" % mag)
            w.Magnitude = mag
        self.Latest = False

    def get_phases(self):
        return [w.Phase for w in self.Waves]

    def set_phases(self, phases):
        """ Sets the relative phase of each pure tone.

        Parameters
        ----------
        phases : list of float
            New phases, expressed as (**radians**), ordered by ascending frequency.

        """
        for w, phase in zip(self.Waves, phases):
            w.Phase = phase
        self.Latest = False

    def randomize(self):
        """ Randomizes each pure tone's phase.
        """
        for w in self.Waves:
            w.Phase = 2*pi*random.random()
        self.Latest = False


def even_spacing(ntraps, center, spacing, mags=None, phases=None, sample_length=None, amp=1.0):
    """ Wrapper function which simplifies defining :class:`~wavgen.waveform.Superposition` objects
     to describe equally spaced traps.

    Parameters
    ----------
    ntraps : int
        Number of optical traps.
    center : int
        Mean or center frequency of the traps.
    spacing : int
        Frequency spacing between traps.
    mags : list of float, optional
        Vector representing relative magnitude of each trap, within [0,1]
        (in order of increasing frequency).
    phases : list of float, optional
        Vector representing initial phases of each trap tone, within [0, 2*pi]
        (in order of increasing frequency).
    sample_length : int, optional
            Length of waveform in samples.
    amp : float, optional
        Amplitude of waveform relative to maximum output voltage.

    Returns
    -------
    :class:`~wavgen.waveform.Superposition`

    """
    freqs = [int(center + spacing*(i - (ntraps-1)/2)) for i in range(ntraps)]
    N = sample_length if sample_length else int(SAMP_FREQ * (2 - ntraps % 2) // spacing) * 32 * REPEAT

    return Superposition(freqs, mags=mags, phases=phases, sample_length=N, amp=amp)


class Sweep(Waveform):
    """ Describes a waveform which smoothly modulates from one :class:`~wavgen.waveform.Superposition`
    to another.

    Attributes
    ----------
    WavesA, WavesB : list of :class:`~wavgen.utilities.Wave`
        Basically full descriptions of 2 :class:`~wavgen.waveform.Superposition` objects;
        i.e. 2 lists of pure tones, including each frequency, magnitude, & phase.
    Damp : float
        Expresses the *change in* :attr:`~wavgen.waveform.Waveform.Amplitude`
        as the waveform modulates from initial to final configuration.

    Warning
    -------
    Sometimes, roughly 1 out of 8 times, the calculation of a ``Sweep`` object will silently fail;
    resulting in correct number of data points, except all 0-valued. To avoid the uncertainty of re-calculation,
    be sure to save ``Sweep`` objects to named files. Also, check calculations with ``Sweep.plot()``.
    """
    def __init__(self, config_a, config_b, sweep_time=None, sample_length=int(16E6)):
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
            sample_length = int(SAMP_FREQ*sweep_time/1000)

        self.WavesA = config_a.Waves
        self.WavesB = config_b.Waves
        self.Damp = (config_b.Amplitude / config_a.Amplitude - 1) / sample_length

        super().__init__(sample_length, max(config_a.Amplitude, config_b.Amplitude))

    def compute(self, p, q):
        N = min(DATA_MAX, self.SampleLength - p*DATA_MAX)
        waveform = np.empty(N, dtype=float)

        ## For each Pure Tone ##
        for j, (a, b) in enumerate(zip(self.WavesA, self.WavesB)):
            fn = a.Frequency / SAMP_FREQ  # Cycles/Sample
            dfn_inc = (b.Frequency - a.Frequency) / (SAMP_FREQ * self.SampleLength)

            phi = a.Phase
            phi_inc = 0 # (b.Phase - phi) / self.SampleLength

            mag = a.Magnitude
            mag_inc = (b.Magnitude - mag) / self.SampleLength

            ## Compute the Wave ##
            for i in range(N):
                n = i + p*DATA_MAX
                dfn = dfn_inc * n / 2  # Sweep Frequency shift
                waveform[i] += (1 + n*self.Damp) * (mag + n*mag_inc) * sin(2 * pi * n * (fn + dfn) + (phi + n*phi_inc))

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

class Sweep1(Waveform):
    """ Describes a waveform which smoothly modulates from one :class:`~wavgen.waveform.Superposition`
    to another with specified hold times on either side of the sweep. Default ramp shape is linear, but there
    are also quadratic and cubic options. All times are inputted in ms.

    Attributes
    ----------
    WavesA, WavesB : list of :class:`~wavgen.utilities.Wave`
        Basically full descriptions of 2 :class:`~wavgen.waveform.Superposition` objects;
        i.e. 2 lists of pure tones, including each frequency, magnitude, & phase.
    Damp : float
        Expresses the *change in* :attr:`~wavgen.waveform.Waveform.Amplitude`
        as the waveform modulates from initial to final configuration.

    """
    def __init__(self, config_a, config_b, hold_time_a = None, hold_time_b = 100, sweep_time=10.0, sample_length = 210E6, ramp = 'linear'):

        assert isinstance(config_a, Superposition) and isinstance(config_b, Superposition)
        assert len(config_a.Waves) == len(config_b.Waves)

        if hold_time_a:
            sample_length = int(SAMP_FREQ*(hold_time_a+sweep_time+hold_time_b)/1000)

        self.WavesA = config_a.Waves
        self.WavesB = config_b.Waves
        self.Damp = (config_b.Amplitude / config_a.Amplitude - 1) / int(SAMP_FREQ*sweep_time/1000)
        self.hold_time_a = hold_time_a
        self.hold_time_b = hold_time_b
        self.sweep_time = sweep_time
        self.ramp = ramp

        super().__init__(sample_length, max(config_a.Amplitude, config_b.Amplitude))

    def compute(self, p, q):
        N = min(DATA_MAX, self.SampleLength - p * DATA_MAX)
        HoldTimeA = int(self.hold_time_a * SAMP_FREQ/1000)
        SweepTime = int(self.sweep_time * SAMP_FREQ/1000)
        waveform = np.empty(N, dtype=float)

        ## For each Pure Tone ##
        for j, (a, b) in enumerate(zip(self.WavesA, self.WavesB)):
            f_a = a.Frequency / SAMP_FREQ  # Cycles/Sample
            f_b = b.Frequency / SAMP_FREQ
            dfn_inc = (b.Frequency - a.Frequency) / (SAMP_FREQ * SweepTime)

            phi = a.Phase
            phi_b = b.Phase
            phi_inc = (b.Phase - phi) / SweepTime

            mag = a.Magnitude
            mag_inc = (b.Magnitude - mag) / SweepTime


            ## Compute the Wave ##
            if self.ramp == 'linear':
                for i in range(N):
                    n = i + p * DATA_MAX
                    dfn = dfn_inc * (n-HoldTimeA)/2  # Sweep Frequency shift

                    if n < HoldTimeA:
                        waveform[i] += mag * sin(2 * pi * n * f_a) # + phi)
                    if HoldTimeA <= n < HoldTimeA + SweepTime:
                        waveform[i] += (1 + (n-HoldTimeA)*self.Damp) * (mag + (n-HoldTimeA) * mag_inc) * sin(2 * pi * (n-HoldTimeA) * (f_a + dfn) + 2 * pi * HoldTimeA * f_a) # + phi + (n-HoldTimeA) * phi_inc)
                    if n >= HoldTimeA + SweepTime:
                        waveform[i] += mag * sin(2 * pi * (n-HoldTimeA-SweepTime) * f_b + 2*pi*(f_a+dfn_inc*SweepTime/2)*SweepTime + 2*pi*f_a*HoldTimeA) #+ phi_b)
            if self.ramp == 'quadratic':
                for i in range(N):
                    n = i + p * DATA_MAX
                    b = 2*(f_b-f_a)/SweepTime**2 # acceleration magnitude

                    if n < HoldTimeA:
                        waveform[i] += mag * sin(2 * pi * n * f_a)
                    if HoldTimeA <= n < HoldTimeA + SweepTime/2:
                        waveform[i] += (1 + (n - HoldTimeA) * self.Damp) * (mag + (n - HoldTimeA) * mag_inc) * sin(2*pi*(f_a*(n-HoldTimeA)+b/3*(n-HoldTimeA)**3) + 2*pi*f_a*HoldTimeA)
                    if HoldTimeA + SweepTime / 2 <= n < HoldTimeA + SweepTime:
                        waveform[i] = np.sin(2 * pi * (f_a * (SweepTime / 2) + b / 3 * (SweepTime/ 2) ** 3) + 2 * pi * f_a * HoldTimeA + 2 * pi * ((f_b + f_a) / 2 * (n - HoldTimeA - SweepTime / 2) - b / 3 * (n - HoldTimeA - SweepTime / 2) ** 3 + b * SweepTime / 2 * (n - HoldTimeA - SweepTime / 2) ** 2))
                    if n >= HoldTimeA + SweepTime:
                        waveform[i] += mag * sin(2 * pi * f_b*(n-HoldTimeA-SweepTime)+2*pi*((f_b+f_a)*SweepTime/4-b/3*(SweepTime/2)**3+b*SweepTime/2*(SweepTime/2)**2) + 2*pi*(f_a*(SweepTime/2)+b/3*(SweepTime/2)**3)+2*np.pi*f_a*HoldTimeA)
            if self.ramp == 'cubic':
                for i in range(N):
                    n = i + p * DATA_MAX
                    a = (2 * f_a - 2 * f_b) / SweepTime ** 3
                    b = (3 * f_b - 3 * f_a) / SweepTime ** 2

                    if n < HoldTimeA:
                        waveform[i] += mag * sin(2 * pi * n * f_a)
                    if HoldTimeA <= n < HoldTimeA + SweepTime:
                        waveform[i] += (1 + (n-HoldTimeA)*self.Damp) * (mag + (n-HoldTimeA) * mag_inc) * sin(2*pi*(a*(n-HoldTimeA)**4/4+b*(n-HoldTimeA)**3/3+f_a*(n-HoldTimeA)) + 2*np.pi*f_a*HoldTimeA)
                    if n >= HoldTimeA + SweepTime:
                        waveform[i] += mag * sin(2 * pi * (n-HoldTimeA-SweepTime) * f_b + 2*pi*(a*SweepTime**4/4+b*SweepTime**3/3+f_a*SweepTime) + 2*pi*f_a*HoldTimeA)

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

class Sweep_loop(Waveform):
    """ Sweeps back and forth between config_a and config_b a specified number of times (n_loops).
    sweep_time indicates the time for one back-and-forth. You can also specify hold times at the beginning and end.
    All times are inputted in ms.
    """
    def __init__(self, config_a, config_b, hold_time_1 = 0.0, hold_time_2 = 0.0, sweep_time=2.0, n_loops = 1, sample_length = None):

        assert isinstance(config_a, Superposition) and isinstance(config_b, Superposition)
        assert len(config_a.Waves) == len(config_b.Waves)

        if hold_time_1:
            sample_length = int(SAMP_FREQ*(hold_time_1+n_loops*sweep_time+hold_time_2)/1000)

        self.WavesA = config_a.Waves
        self.WavesB = config_b.Waves
        self.Damp = (config_b.Amplitude / config_a.Amplitude - 1) / int(SAMP_FREQ*sweep_time/1000)
        self.hold_time_1 = hold_time_1
        self.hold_time_2 = hold_time_2
        self.sweep_time = sweep_time
        self.n_loops = n_loops

        super().__init__(sample_length, max(config_a.Amplitude, config_b.Amplitude))

    def compute(self, p, q):
        N = min(DATA_MAX, self.SampleLength - p * DATA_MAX)
        HoldTime1 = int(self.hold_time_1 * SAMP_FREQ/1000)
        SweepTime = int(self.sweep_time * SAMP_FREQ/1000)
        waveform = np.empty(N, dtype=float)

        ## For each Pure Tone ##
        for j, (a, b) in enumerate(zip(self.WavesA, self.WavesB)):
            f_a = a.Frequency / SAMP_FREQ  # Cycles/Sample
            f_b = b.Frequency / SAMP_FREQ
            df = 2* (b.Frequency - a.Frequency) / (SAMP_FREQ * SweepTime) # one back-and-forth per sweep time

            phi = a.Phase
            phi_b = b.Phase
            phi_inc = (b.Phase - phi) / SweepTime

            mag = a.Magnitude
            mag_inc = (b.Magnitude - mag) / SweepTime


            ## Compute the Wave ##
            for i in range(N):
                n = i + p * DATA_MAX

                if n < HoldTime1:
                    waveform[i] = np.sin(2 * np.pi * f_a * n)
                for j in range(self.n_loops):
                    if HoldTime1 + j * SweepTime <= n < HoldTime1 + (j + 1 / 2) * SweepTime:
                        waveform[i] = np.sin(2 * np.pi * (f_a + df * (n - HoldTime1 - j * SweepTime) / 2) * (
                                    n - HoldTime1 - j * SweepTime) + 2 * np.pi * j * (
                                                         f_b - df * (SweepTime / 2) / 2) * (
                                                         SweepTime / 2) + 2 * np.pi * j * (
                                                         f_a + df * (SweepTime / 2) / 2) * (
                                                         SweepTime / 2) + 2 * np.pi * f_a * HoldTime1)
                    if HoldTime1 + (j + 1 / 2) * SweepTime <= n < HoldTime1 + (j + 1) * SweepTime:
                        waveform[i] = np.sin(2 * np.pi * (f_b - df * (n - HoldTime1 - (j + 1 / 2) * SweepTime) / 2) * (
                                    n - HoldTime1 - (j + 1 / 2) * SweepTime) + 2 * np.pi * (
                                                         f_a + df * (SweepTime / 2) / 2) * (
                                                         SweepTime / 2) + 2 * np.pi * j * (
                                                         f_b - df * (SweepTime / 2) / 2) * (
                                                         SweepTime / 2) + 2 * np.pi * j * (
                                                         f_a + df * (SweepTime / 2) / 2) * (
                                                         SweepTime / 2) + 2 * np.pi * f_a * HoldTime1)
                if HoldTime1 + self.n_loops * SweepTime <= n:
                    waveform[i] = np.sin(2 * np.pi * f_a * (n - HoldTime1 - self.n_loops * SweepTime) + 2 * np.pi * (
                                f_b - df * (SweepTime / 2) / 2) * (SweepTime / 2) + 2 * np.pi * (
                                                     f_a + df * (SweepTime / 2) / 2) * (SweepTime / 2) + 2 * np.pi * (
                                                     self.n_loops - 1) * (f_b - df * (SweepTime / 2) / 2) * (
                                                     SweepTime / 2) + 2 * np.pi * (self.n_loops - 1) * (
                                                     f_a + df * (SweepTime / 2) / 2) * (
                                                     SweepTime / 2) + 2 * np.pi * f_a * HoldTime1)

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

class LinearTest(Waveform):
    def __init__(self):

        sample_length = 2E5


        super().__init__(sample_length)

    def compute(self, p, q):
        N = min(DATA_MAX, self.SampleLength - p * DATA_MAX)
        waveform = np.empty(N, dtype=float)

            ## Compute the Wave ##
        for i in range(N):
            n = i + p * DATA_MAX
            waveform[i] = n/self.SampleLength

        ## Send the results to Parent ##
        q.put((p, waveform, max(waveform.max(), abs(waveform.min()))))

######### HS1 Class #########
class HS1(Waveform):
    """ Embodies a Hyperbolic-Secant Pulse.

    Attributes
    ----------
    Tau : float
        Characteristic length of pulse; expressed in samples.
    Center : float
        The frequency at which the sweep is centered about; expressed as oscillations per sample.
    BW : float
        Bandwith or width of the range the frequency is swooped across; expressed as oscillations per sample.

    See Also
    --------
    `B Peaudecerf et al 2019 New J. Phys. 21 013020 (Section 3.1) <file:../_static/pap1.pdf>`_
        Relevant context. Used to verify functional form.

    `M. Khudaverdyan et al 2005 Phys. Rev. A 71, 031404(R) <file:../_static/pap2.pdf>`_
        Slightly more relevant...yet less useful.
    """
    def __init__(self, pulse_time, center_freq, sweep_width, duration=None, amp=1.0):
        """
        Parameters
        ----------
        pulse_time : float
            Sets the characteristic time.
        center_freq : int
            The frequency sweep is centered about this value.
        sweep_width : int
            How wide, in frequency, the sweep swoops.
        duration : float, optional
            Used to fix the waveform duration, while the pulse width itself is unaffected.
            Otherwise, we follow a recommendation from the first reference above.
        amp : float, optional
            Amplitude of waveform relative to maximum output voltage.
        """
        if duration:
            sample_length = int(SAMP_FREQ * duration)
        else:
            sample_length = int(SAMP_FREQ * pulse_time * 5)
        super().__init__(sample_length, amp)

        self.Tau = pulse_time * SAMP_FREQ
        self.Center = center_freq / SAMP_FREQ
        self.BW = sweep_width / SAMP_FREQ

    def compute(self, p, q):
        N = min(DATA_MAX, self.SampleLength - p*DATA_MAX)
        waveform = np.empty(N, dtype=float)

        ## Compute the Wave ##
        for i in range(N):
            n = i + p*DATA_MAX

            d = 2*(n - self.SampleLength/2)/self.Tau  # 2(t - T/2)/tau

            try:
                arg = n * self.Center + (self.Tau * self.BW / 4) * log(cosh(d))
                amp = 1 / cosh(d)
            except OverflowError:
                arg = n * self.Center + (self.Tau * self.BW / 4) * log(maxsize)
                amp = 0

            waveform[i] = amp * sin(2 * pi * arg)

        ## Send results to Parent ##
        q.put((p, waveform, max(waveform.max(), abs(waveform.min()))))

    def config_dset(self, dset):
        ## Contents ##
        dset.attrs.create('pulse_time', data=self.Tau / SAMP_FREQ)
        dset.attrs.create('center_freq', data=self.Center * SAMP_FREQ)
        dset.attrs.create('sweep_width', data=self.BW * SAMP_FREQ)
        dset.attrs.create('duration', data=self.SampleLength / SAMP_FREQ)

        ## Table of Contents ##
        dset.attrs.create('keys', data=['pulse_time', 'center_freq', 'sweep_width', 'duration'])

        return dset

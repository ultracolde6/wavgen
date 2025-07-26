"""
Waveform Generation Module

This module provides various waveform classes for generating different types of
waveforms used in optical tweezer experiments. All classes inherit from the base
Waveform class and implement specific waveform generation algorithms.

The module includes:
- Superposition: Static trap configuration with multiple frequency components
- Sweep: Smooth modulation between two superposition configurations
- Sweep1: Sweep with hold times and configurable ramp shapes
- Sweep_loop: Looping sweep with multiple iterations
- Sweep_sequence: Sequence-based sweep operations
- Sweep_crop: Cropped sweep with specific sections
- LinearTest: Simple linear test waveform
- HS1: High-speed sweep waveform
- SuperpositionJiggle: Frequency-modulated superposition
- SingleJiggle: Single frequency-modulated component

Each waveform class implements specific computation algorithms and provides
methods for configuration, computation, and data storage. The module also includes
helper functions like even_spacing for creating common trap configurations.
"""

from math import pi, sin, cosh, log
from .waveform_base import Waveform
from .utilities import Wave
from easygui import msgbox
from sys import maxsize
from .constants import *
from math import inf
import numpy as np
import random
import h5py
from wavgen.utilities import *
from scipy import signal
from fractions import Fraction


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

            # lcm = inf
            # for f in freqs:
            #     digits = 0
            #     while f%10 == 0:
            #         f = f // 10
            #         digits += 1
            #     lcm = min(digits, lcm)
            #     """
            #     + 1
            #     """
            # print(lcm)
            # sample_length = (SAMP_FREQ / 10**lcm) * 32 * REPEAT
            gcd = np.gcd.reduce(np.array(freqs, dtype=int))
            # sample_length = 32*Fraction(SAMP_FREQ*REPEAT, gcd).numerator
            sample_length = Fraction(SAMP_FREQ*REPEAT, gcd).numerator
            while sample_length%32 != 0:
                sample_length *= 2
            print(SAMP_FREQ*REPEAT)
            print(gcd)
            print(f"Sample_length={sample_length}")
            # print((SAMP_FREQ / 10**lcm) * 32 * REPEAT)
            while sample_length < 384:
                sample_length += sample_length
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
        """Compute a portion of the superposition waveform.
        
        Calculates the waveform by summing all pure tone components
        for the specified interval. This method is dispatched to parallel processes.
        
        Parameters
        ----------
        p : int
            Index indicating which interval of the waveform to calculate.
        q : multiprocessing.Queue
            Queue for returning computation results to parent process.
        """
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

                ## hard coded random phase, need to be improved
                # waveform[i] += mag * sin(2 * pi * n * fn + phi + 0.1*(random.random()-0.5))
                ## waveform without random phase
                waveform[i] += mag * sin(2 * pi * n * fn + phi)

        ## Send the results to Parent ##
        # print(f'max = {max(waveform.max(), abs(waveform.min()))}')
        q.put((p, waveform, max(waveform.max(), abs(waveform.min()))))
        # return max(waveform.max(), abs(waveform.min()))


    def config_dset(self, dset):
        """Configure HDF5 dataset with superposition waveform metadata.
        
        Sets up the dataset attributes including frequencies, magnitudes,
        phases, and sample length for the superposition waveform.
        
        Parameters
        ----------
        dset : h5py.Dataset
            The HDF5 dataset to configure with superposition attributes.
            
        Returns
        -------
        h5py.Dataset
            The configured dataset with metadata attributes added.
        """
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
        """Get the phases of all pure tones in the superposition.
        
        Returns
        -------
        list of float
            Phase values in radians for each pure tone, ordered by increasing frequency.
        """
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
        """Compute a portion of the sweep waveform.
        
        Calculates the waveform by interpolating between two superposition
        configurations for the specified interval. This method is dispatched to parallel processes.
        
        Parameters
        ----------
        p : int
            Index indicating which interval of the waveform to calculate.
        q : multiprocessing.Queue
            Queue for returning computation results to parent process.
        """
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
        """Configure HDF5 dataset with sweep waveform metadata.
        
        Sets up the dataset attributes including frequencies, magnitudes,
        and phases for both initial and final configurations.
        
        Parameters
        ----------
        dset : h5py.Dataset
            The HDF5 dataset to configure with sweep attributes.
            
        Returns
        -------
        h5py.Dataset
            The configured dataset with metadata attributes added.
        """
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
            mag_b = b.Magnitude


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
                        waveform[i] += mag_b * sin(2 * pi * (n-HoldTimeA-SweepTime) * f_b + 2*pi*(f_a+dfn_inc*SweepTime/2)*SweepTime + 2*pi*f_a*HoldTimeA) #+ phi_b)
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
                        waveform[i] += mag_b * sin(2 * pi * f_b*(n-HoldTimeA-SweepTime)+2*pi*((f_b+f_a)*SweepTime/4-b/3*(SweepTime/2)**3+b*SweepTime/2*(SweepTime/2)**2) + 2*pi*(f_a*(SweepTime/2)+b/3*(SweepTime/2)**3)+2*np.pi*f_a*HoldTimeA)
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
                        waveform[i] += mag_b * sin(2 * pi * (n-HoldTimeA-SweepTime) * f_b + 2*pi*(a*SweepTime**4/4+b*SweepTime**3/3+f_a*SweepTime) + 2*pi*f_a*HoldTimeA)

            if self.ramp == 'cosine':
                for i in range(N):
                    n = i + p * DATA_MAX
                    w_a = 2*np.pi*f_a
                    w_b = 2*np.pi*f_b
                    A = (w_b-w_a)/SweepTime
                    if n < HoldTimeA:
                        waveform[i] += mag * sin(w_a*n+phi)
                    if HoldTimeA <= n < HoldTimeA + SweepTime:
                        waveform[i] += (1 + (n - HoldTimeA) * self.Damp) * (mag + (n - HoldTimeA) * mag_inc) * sin(
                            w_a*HoldTimeA + phi + A*((n-HoldTimeA)**2/2 + (SweepTime/(2*np.pi))**2*np.cos(2*np.pi*(n-HoldTimeA)/SweepTime)) + w_a*(n-HoldTimeA) - A*(SweepTime/(2*np.pi))**2)
                    if n >= HoldTimeA + SweepTime:
                        waveform[i] += mag_b * sin(w_a*HoldTimeA + phi + A*(SweepTime**2/2 + (SweepTime/(2*np.pi))**2) + w_a*SweepTime + w_b*(n-HoldTimeA-SweepTime) -A *(SweepTime/(2*np.pi))**2)

        ## Send the results to Parent ##
        q.put((p, waveform, max(waveform.max(), abs(waveform.min()))))

    def config_dset(self, dset):
        """Configure HDF5 dataset with sweep waveform metadata.
        
        Sets up the dataset attributes including frequencies, magnitudes,
        and phases for both initial and final configurations.
        
        Parameters
        ----------
        dset : h5py.Dataset
            The HDF5 dataset to configure with sweep attributes.
            
        Returns
        -------
        h5py.Dataset
            The configured dataset with metadata attributes added.
        """
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
    All times are inputted in ms. Cosine sweep only does one back-and-forth.
    """
    def __init__(self, config_a, config_b, hold_time_1 = 0.0, hold_time_2 = 0.0, sweep_time=2.0, n_loops = 1, sample_length = None, ramp = 'cosine'):

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
        self.ramp = ramp

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
            if self.ramp == 'linear':
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

            if self.ramp == 'cosine':
                wA = 2*np.pi*f_a
                wB = 2*np.pi*f_b
                A = 2*(wB-wA)/SweepTime
                for i in range(N):
                    n = i + p * DATA_MAX

                    if n < HoldTime1:
                        waveform[i] += mag*np.sin(wA * n + phi)
                    if HoldTime1 <= n < HoldTime1 + SweepTime/2:
                        waveform[i] += mag*np.sin(wA * HoldTime1 + phi + A * (
                                    (n - HoldTime1) ** 2 / 2 + (SweepTime / (4 * np.pi)) ** 2 * np.cos(
                                4 * np.pi * (n - HoldTime1) / SweepTime)) + wA * (n - HoldTime1) - A * (
                                               SweepTime / (4 * np.pi)) ** 2)
                    if HoldTime1 + SweepTime / 2 <= n < HoldTime1 + SweepTime:
                        waveform[i] += mag*np.sin(wA * HoldTime1 + phi + A * (
                                    SweepTime ** 2 * (1 / 8 + 1 / (16 * np.pi ** 2))) + wA * SweepTime / 2 - A * (
                                               (n - (HoldTime1 + SweepTime / 2)) ** 2 / 2 + (
                                                   SweepTime / (4 * np.pi)) ** 2 * np.cos(
                                           4 * np.pi * (n - (HoldTime1 + SweepTime / 2)) / SweepTime)) + wB * (
                                               n - (HoldTime1 + SweepTime / 2)))
                    if HoldTime1 + SweepTime <= n:
                        waveform[i] += mag*np.sin(wA * (
                                    HoldTime1 + SweepTime / 2 + n - HoldTime1 - SweepTime) + phi + wB * SweepTime / 2)

        ## Send the results to Parent ##
        q.put((p, waveform, max(waveform.max(), abs(waveform.min()))))

    def config_dset(self, dset):
        """Configure HDF5 dataset with sweep waveform metadata.
        
        Sets up the dataset attributes including frequencies, magnitudes,
        and phases for both initial and final configurations.
        
        Parameters
        ----------
        dset : h5py.Dataset
            The HDF5 dataset to configure with sweep attributes.
            
        Returns
        -------
        h5py.Dataset
            The configured dataset with metadata attributes added.
        """
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


class Sweep_sequence(Waveform):
    """ Describes a waveform which smoothly modulates from one :class:`~wavgen.waveform.Superposition`
    to another with specified sweep time. Default ramp shape is cosine. We add on a bit of static waveform at the end
    of the sweep to ensure the initial and final phases match. All times are inputted in ms. Note: linear one does not work!
    Also note: when running in sequence replay mode, the default sweep_time needs to be set to the actual sweep_time. Not sure why.

    Attributes
    ----------
    WavesA, WavesB : list of :class:`~wavgen.utilities.Wave`
        Basically full descriptions of 2 :class:`~wavgen.waveform.Superposition` objects;
        i.e. 2 lists of pure tones, including each frequency, magnitude, & phase.
    Damp : float
        Expresses the *change in* :attr:`~wavgen.waveform.Waveform.Amplitude`
        as the waveform modulates from initial to final configuration.

    """
    def __init__(self, config_a, config_b, sweep_time = None, sample_length = None, ramp = 'cosine', segment = True):

        assert isinstance(config_a, Superposition) and isinstance(config_b, Superposition)
        assert len(config_a.Waves) == len(config_b.Waves)
        if sweep_time:
            sample_length = int(SAMP_FREQ * sweep_time / 1000)
        if sample_length % 32:
            sample_length = int(sample_length - sample_length % 32)
        sweep_time = 1000*sample_length/SAMP_FREQ
        # print(f'sample_length = {sample_length}')
        self.WavesA = config_a.Waves
        self.WavesB = config_b.Waves
        self.Damp = (config_b.Amplitude / config_a.Amplitude - 1) / int(SAMP_FREQ*sweep_time/1000)
        self.ramp = ramp
        self.segment = segment
        super().__init__(sample_length, max(config_a.Amplitude, config_b.Amplitude))

    def compute(self, p, q):
        N = min(DATA_MAX, self.SampleLength - p * DATA_MAX)
        waveform = np.empty(N, dtype=float)
        phase = np.empty(N, dtype=float)



        ## For each Pure Tone ##
        for j, (a, b) in enumerate(zip(self.WavesA, self.WavesB)):
            f_a = a.Frequency / SAMP_FREQ  # Cycles/Sample
            f_b = b.Frequency / SAMP_FREQ
            wA = 2*np.pi*f_a
            wB = 2*np.pi*f_b
            phi_A = a.Phase
            phi_B = b.Phase
            # if phi_A - phi_B > np.pi: phi_B += 2*np.pi
            # if phi_A - phi_B < -np.pi: phi_B -= 2*np.pi
            T = self.SampleLength


            ## Compute the Wave ##
            # if self.ramp == 'linear':
            #     m = 1 / (2 * np.pi) * (
            #                 2 * np.pi * np.min((f_b, f_a)) * self.SampleLength + 1 / 2 * self.SampleLength * abs(
            #             2 * np.pi * f_b - 2 * np.pi * f_a))
            #     M = int(m + 1)
            #     t = self.SampleLength - 2 * (2 * (M - m) * np.pi) / abs(2 * np.pi * f_b - 2 * np.pi * f_a)
            #     print(t)
            #     df = (b.Frequency - a.Frequency) / (SAMP_FREQ * t)
            #     for i in range(N):
            #         n = i + p * DATA_MAX
            #
            #         if f_b - f_a > 0:
            #             if n < t:
            #                 waveform[i] += np.sin(2*np.pi*(f_a+df*n/2)*n + phi)
            #             if n >= t:
            #                 waveform[i] += np.sin(2*np.pi*f_b*(n-t) + 2*np.pi*(f_a+df*t/2)*t + phi)
            #         else:
            #             if n < self.SampleLength - t:
            #                 waveform[i] += np.sin(2 * np.pi * f_a * n + phi)
            #             if self.SampleLength - t[j] <= n:
            #                 waveform[i] += np.sin(2 * np.pi * (f_a + df * (n - (self.SampleLength - t)) / 2) * (
            #                             n - (self.SampleLength - t)) + phi + 2 * np.pi * f_a * (
            #                                           self.SampleLength - t))

            # if self.ramp == 'cosine' and self.segment is not True:
            #     wA = 2*np.pi*f_a
            #     wB = 2*np.pi*f_b
            #     A = (wB - wA) / self.SampleLength
            #     m = 1 / (2 * np.pi) * (wA * self.SampleLength + A * self.SampleLength ** 2 / 2)
            #     if wA != wB:
            #         if wA - wB < 0:
            #             M = int(m + 1)
            #         else:
            #             M = int(m)
            #         t = int((2 * np.pi * M - wB * self.SampleLength) * 2 / (wA - wB))
            #         print(t)
            #         A0 = (wB - wA) / t
            #         dphi = (b.Phase - a.Phase)/ self.SampleLength
            #         for i in range(N):
            #             n = i + p * DATA_MAX
            #             if n < t:
            #                 waveform[i] += np.sin(wA * n + A0 * n ** 2 / 2 + A0 * (
            #                             t / (2 * np.pi)) ** 2 * np.cos(2 * np.pi * n / t) - A0 * (
            #                                                    t / (2 * np.pi)) ** 2 + phi + dphi*n)
            #             if n >= t:
            #                 waveform[i] += np.sin(wB * (n - t) + wA * t + A0 * t ** 2 / 2 + A0 * (t / (2 * np.pi)) ** 2 * np.cos(2 * np.pi) - A0 * (
            #                             t / (2 * np.pi)) ** 2 + phi + dphi*n)
            #     else:
            #         phi_A = a.Phase
            #         phi_B = b.Phase
            #         dphi = (phi_B-phi_A - ((wA*self.SampleLength) % (2*np.pi)))/self.SampleLength
            #         for i in range(N):
            #             n = i + p * DATA_MAX
            #             waveform[i] += np.sin(wA * n + phi_A + dphi*n)

            if self.ramp == 'shiftedlinear':
                delta_phi = (np.pi + phi_B - phi_A - (wA + wB) / 2 * T) % (2 * np.pi) - np.pi
                dphi = delta_phi / T
                for i in range(N):
                    n = i + p * DATA_MAX
                    waveform[i] += np.sin(phi_A + (wA + dphi) * n + ((wB - wA) / 2 / T) * n ** 2)

            # if self.ramp == 'almostlinear':
            if self.ramp == 'linear':
                delta_phi = (np.pi + phi_B - phi_A - (wA + wB) / 2 * T) % (2 * np.pi) - np.pi
                for i in range(N):
                    n = i + p * DATA_MAX
                    waveform[i] += np.sin(phi_A + (wA) * n + ((wB - wA) / 2 / T) * n ** 2 \
                                          + delta_phi * (3 * T - 2 * n) * n ** 2 / T ** 3)

            if self.ramp == 'shiftedcosine':
                print(f'T={T}, N={N}')
                delta_phi = (np.pi + phi_B - phi_A - (wA + wB) / 2 * T) % (2 * np.pi) - np.pi
                dphi = delta_phi / T
                A0 = (wB - wA) / T
                for i in range(N):
                    n = i + p * DATA_MAX
                    waveform[i] += np.sin(phi_A + (wA + dphi) * n \
                                          + A0 * n ** 2 / 2 \
                                          + A0 * (T / (2 * np.pi)) ** 2 * np.cos(2 * np.pi * n / T) \
                                          - A0 * (T / (2 * np.pi)) ** 2)
            # if self.ramp == 'almostcosine':
            if self.ramp == 'cosine':
                delta_phi = (np.pi + phi_B - phi_A - (wA + wB) / 2 * T) % (2 * np.pi) - np.pi
                A0 = (wB - wA) / T
                for i in range(N):
                    n = i + p * DATA_MAX
                    waveform[i] += np.sin(phi_A + wA * n \
                                          + A0 * n ** 2 / 2 \
                                          + A0 * (T / (2 * np.pi)) ** 2 * np.cos(2 * np.pi * n / T) \
                                          - A0 * (T / (2 * np.pi)) ** 2 \
                                          + delta_phi * (3 * T - 2 * n) * n ** 2 / T ** 3)
            # if self.ramp == 'cosine' and self.segment is True:
            #     # break the sweep up into x segments
            #     x = 2
            #     while self.SampleLength % x != 0:
            #         x += 1
            #     print(f'choosing x = {x}')
            #     phi_x_list = []
            #     phi_x_list.append(phi)
            #     for i in range(x - 1):
            #         phi_x_list.append((rp[i + j + 1] + phi_x_list[i]))
            #     phi_x_list.append(phi + 4 * np.pi)
            #     phi_x_list = np.array(phi_x_list)
            #     # print(f'phi_x_list = {phi_x_list}')
            #     wA = 2 * np.pi * f_a
            #     wB = 2 * np.pi * f_b
            #     A = (wB - wA) / self.SampleLength
            #     m = 1 / (2 * np.pi) * (wA * self.SampleLength + A * self.SampleLength ** 2 / 2)
            #     if wA != wB:
            #         if wA - wB < 0:
            #             M = int(m + 1)
            #         else:
            #             M = int(m)
            #         t = int((2 * np.pi * M - wB * self.SampleLength) * 2 / (wA - wB))
            #         print(t)
            #         A0 = (wB - wA) / t
            #         dphi = (b.Phase - a.Phase) / self.SampleLength
            #         dphi_x_list = []
            #         durSeg = int(self.SampleLength / x)
            #         for seg in range(x):
            #             dphi_x_list.append((phi_x_list[seg + 1] - phi_x_list[seg]) / durSeg)
            #         # print(f'dphi_x_list = {dphi_x_list}')
            #
            #         for i in range(N):
            #             n = i + p * DATA_MAX
            #             if n < t:
            #                 phase[i] = wA * n + A0 * n ** 2 / 2 + A0 * (
            #                         t / (2 * np.pi)) ** 2 * np.cos(2 * np.pi * n / t) - A0 * (
            #                                               t / (2 * np.pi)) ** 2 + phi + dphi * n
            #                 for seg in range(x):
            #                     if durSeg * seg <= n < durSeg * (seg + 1):
            #                         phase[i] += dphi_x_list[seg] * (n - durSeg * seg)
            #                         for k in range(seg):
            #                             phase[i] += dphi_x_list[k] * durSeg
            #                 waveform[i] += np.sin(phase[i])
            #             if n >= t:
            #                 phase[i] = wB * (n - t) + wA * t + A0 * t ** 2 / 2 + A0 * (t / (2 * np.pi)) ** 2 * np.cos(
            #                         2 * np.pi) - A0 * (t / (2 * np.pi)) ** 2 + phi + dphi * n
            #                 for seg in range(x):
            #                     if durSeg * seg <= n < durSeg * (seg + 1):
            #                         phase[i] += dphi_x_list[seg] * (n - durSeg * seg)
            #                         for k in range(seg):
            #                             phase[i] += dphi_x_list[k] * durSeg
            #                 waveform[i] += np.sin(phase[i])
            #     else:
            #         phi_A = a.Phase
            #         phi_B = b.Phase
            #         dphi = (phi_B - phi_A - ((wA * self.SampleLength) % (2 * np.pi))) / self.SampleLength
            #         for i in range(N):
            #             n = i + p * DATA_MAX
            #             waveform[i] += np.sin(wA * n + phi_A + dphi * n)
        ## Send the results to Parent ##
        # print(f'max = {max(waveform.max(), abs(waveform.min()))}')
        q.put((p, waveform, max(waveform.max(), abs(waveform.min()))))
        # return max(waveform.max(), abs(waveform.min()))

    def config_dset(self, dset):
        """Configure HDF5 dataset with sweep waveform metadata.
        
        Sets up the dataset attributes including frequencies, magnitudes,
        and phases for both initial and final configurations.
        
        Parameters
        ----------
        dset : h5py.Dataset
            The HDF5 dataset to configure with sweep attributes.
            
        Returns
        -------
        h5py.Dataset
            The configured dataset with metadata attributes added.
        """
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

class Sweep_crop(Waveform):

    def __init__(self, wave, config_a, config_b, sweep_time =1.0, hold_time_a = 100.0, section = None, sample_length = None):
        assert wave is not None, "Invalid datapath"
        assert isinstance(config_a, Superposition) and isinstance(config_b, Superposition)
        assert len(config_a.Waves) == len(config_b.Waves)
        self.WavesA = config_a.Waves
        self.WavesB = config_b.Waves
        self.Damp = (config_b.Amplitude / config_a.Amplitude - 1) / int(SAMP_FREQ*sweep_time/1000)
        self.Wave = wave
        self.section = section
        self.hold_time_a = int(hold_time_a * 1e-3 * SAMP_FREQ)  # samples
        self.sweep_time = int(sweep_time * 1e-3 * SAMP_FREQ) # this is in samples even though it says time
        self.start_time = int(self.hold_time_a - config_a.SampleLength)
        self.end_sweep = int(self.hold_time_a + self.sweep_time)
        self.end_time = int(self.end_sweep + config_b.SampleLength)

        if section == 'A':
            sample_length = config_a.SampleLength
        if section == 'AB':
            sample_length = int(sweep_time * 1e-3 * SAMP_FREQ) #self.Wave[self.hold_time_a:self.end_sweep]
        if section == 'B':
            sample_length = config_b.SampleLength

        if sample_length % 32:
            sample_length = int(sample_length - sample_length % 32)
        super().__init__(sample_length, max(config_a.Amplitude, config_b.Amplitude))


    def compute(self, p, q):
        if self.section == 'A':
            N = min(DATA_MAX, self.SampleLength - p * DATA_MAX)
            waveform = np.zeros(N, dtype=float)
            for i in range(N):
                n = i + p*DATA_MAX
                waveform[i] = self.Wave[self.start_time:self.hold_time_a][n]
        if self.section == 'AB':
            N = min(DATA_MAX, self.SampleLength - p * DATA_MAX)
            waveform = np.zeros(N, dtype=float)
            for i in range(N):
                n = i + p*DATA_MAX
                waveform[i] = self.Wave[self.hold_time_a:self.end_sweep][n]
        if self.section == 'B':
            waveform = self.Wave[self.end_sweep:self.end_time]
        print(waveform)
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
        waveform = Sweep1(supA, supB)

        return cls(waveform, supA, supB, sample_length=sample_length)

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



class SuperpositionJiggle(Waveform):
    """ A partially static, partially jiggling trap configuration.

    Attributes
    ----------

    Jiggle_Waves : list of :class:`~wavgen.utilities.JiggleWave`
        The list of modulated pure tones. Each object holds a carrier frequency,
        carrier magnitude, and carrier phase,
        as well as a modulation frequency, carrier magnitude, and carrier phase

    Hint
    ----
    There are now 3 relevant **amplitudes** here:
    :meth:`Output Voltage Limit <wavgen.card.Card.setup_channels>`,
    :attr:`Waveform Amplitude <wavgen.waveform.Waveform.Amplitude>`, & the
    :attr:`amplitudes of each pure tone <wavgen.utilities.Wave.Magnitude>`
    composing a superposition. Each one is expressed as a fraction of the previous.

    """
    def __init__(self, base_freqs, mod_freqs=None, base_amps=None, mod_amps=None, base_phases=None, mod_phases=None, mod_forms=None, sample_length=None, amp=1.0):
        """ Provides several options for defining waveform duration.

        Parameters
        ----------
        base_freqs :  list of int, in units of Hz

        mod_freqs : list of int, in units of Hz

        mod_amps : list of float, in units of Hz, so the phase modulation amplitude is actually (mod_amp/mod_freq)

        base_phases:  list of float, optional
            base tone initial phase, defualts to be 0
            ...
        sample_length : int, optional
            Length of waveform in samples.
        amp : float, optional
            Amplitude of waveform relative to maximum output voltage.
        """
        # base_freqs.sort()

        ## Applies passed Magnitudes or Phases ##
        if mod_freqs is None:
            mod_freqs = np.zeros(len(base_freqs))
        if base_amps is None:
            base_amps = np.ones(len(base_freqs))
        if mod_amps is None:
            mod_amps = np.zeros(len(base_freqs))
        if base_phases is None:
            # print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            base_phases = np.zeros(len(base_freqs))
        if mod_phases is None:
            mod_phases = np.zeros(len(base_freqs))
        if mod_forms is None:
            mod_forms = np.empty(len(base_freqs), dtype='object')
            mod_forms[:] = "Off"

        for ii, form in enumerate(mod_forms):
            if form == "Off":
                mod_amps[ii] = 0
                mod_freqs[ii] = 0
                mod_phases[ii] = 0

        f_array = np.concatenate((base_freqs, mod_freqs))
        f_array = f_array[np.nonzero(f_array)]

        ## Find the LeastCommonMultiple ##
        if sample_length is None:

            # lcm = inf
            # for f in f_array:
            #     digits = 0
            #     while f%10 == 0 and digits<100:
            #         f = f // 10
            #         digits += 1
            #     lcm = min(digits, lcm)
            #     """
            #     + 1
            #     """
            # sample_length = (SAMP_FREQ / 10**lcm) * 32 * REPEAT
            gcd = np.gcd.reduce(np.array(f_array, dtype=int))
            print('here')
            print(f_array)
            print(SAMP_FREQ)
            print(gcd)
            sample_length = 32 * Fraction(SAMP_FREQ * REPEAT, gcd).numerator
            print(f'sample length = {sample_length}')
            while sample_length < 384:
                sample_length += sample_length
            msg = "Waveform will not be an integer # of periods.\nYou may want to calculate a sample length manually"
        if sample_length % 1:
            msgbox(msg, "Warning")
        else:
            sample_length = int(sample_length)



        assert np.min(f_array) >= SAMP_FREQ/sample_length, "Frequency is below resolution. Increase sample length."
        assert np.max(f_array) < SAMP_FREQ / 2, ("Frequency %d must below Nyquist: %d" % (np.max(f_array), SAMP_FREQ / 2))
        assert len(base_amps) == len(base_freqs) == len(base_phases)==len(mod_amps) == len(mod_freqs) == len(mod_phases) == len(mod_forms), "Parameter size mismatch!"

        ## Initialize ##
        self.JiggleWaves = [JiggleWave(bf, ba, bp, mf, ma, mp) for bf, ba, bp, mf, ma, mp in zip(base_freqs, base_amps, base_phases, mod_freqs, mod_amps, mod_phases)]
        self.JiggleForms = mod_forms
        super().__init__(sample_length, amp)

    def compute(self, p, q):
        N = min(DATA_MAX, self.SampleLength - p*DATA_MAX)
        waveform = np.zeros(N, dtype=float)

        ## For each Pure Tone ##
        for j, w in enumerate(self.JiggleWaves):
            mod_form = self.JiggleForms[j]
            f0 = w.BaseFrequency / SAMP_FREQ
            phi0 = w.BasePhase
            mag0 = w.BaseMagnitude
            f1 = w.ModFrequency / SAMP_FREQ
            phi1 = w.ModPhase
            if w.ModFrequency != 0:
                mag1 = w.ModMagnitude/w.ModFrequency
            else:
                mag1 = 0
            ## Compute the Wave ##
            for i in range(N):
                n = i + p * DATA_MAX
                if mod_form == "Off":
                    waveform[i] += mag0 * sin(2 * pi * f0 * n + phi0 )
                if mod_form == "Sine":
                    waveform[i] += mag0 * sin(2 * pi * f0 * n + phi0 + mag1 * sin(2 * pi * f1 * n + phi1))
                if mod_form == "Toggle":
                    waveform[i] += mag0 * sin(
                        2 * pi * f0 * n + phi0 + np.pi/2 * mag1 * signal.sawtooth(2 * pi * f1 * n + phi1, 0.5))


        ## Send the results to Parent ##
        # print(f'max = {max(waveform.max(), abs(waveform.min()))}')
        q.put((p, waveform, max(waveform.max(), abs(waveform.min()))))
        # return max(waveform.max(), abs(waveform.min()))


    def config_dset(self, dset):
        ## Contents ##
        dset.attrs.create('base_freqs', data=np.array([w.BaseFrequency for w in self.JiggleWaves]))
        dset.attrs.create('base_mags', data=np.array([w.BaseMagnitude for w in self.JiggleWaves]))
        dset.attrs.create('base_phases', data=np.array([w.BasePhase for w in self.JiggleWaves]))
        dset.attrs.create('mod_freqs', data=np.array([w.ModFrequency for w in self.JiggleWaves]))
        dset.attrs.create('mod_mags', data=np.array([w.ModMagnitude for w in self.JiggleWaves]))
        dset.attrs.create('mod_phases', data=np.array([w.ModPhase for w in self.JiggleWaves]))
        dset.attrs.create('mod_forms', data=np.array(self.JiggleForms))
        dset.attrs.create('sample_length', data=self.SampleLength)

        ## Table of Contents ##
        dset.attrs.create('keys', data=['base_freqs', 'base_mags', 'base_phases', 'mod_freqs', 'mod_mags', 'mod_phases', 'mod_forms', 'sample_length'])

        return dset
    #

    @classmethod
    def from_file(cls, **kwargs):
        # print(kwargs)
        base_freqs, base_amps, base_phases, mod_freqs, mod_amps, mod_phases, mod_forms, sample_length = kwargs.values()
        print(f"base_freqs={base_freqs}")
        supA = SuperpositionJiggle(base_freqs, mod_freqs, base_amps, mod_amps, base_phases, mod_phases, mod_forms)
        # supB = Superposition(freqsB, magsB, phasesB)

        return cls(supA, sample_length=sample_length)

    # @classmethod
    # def from_file(cls, **kwargs):
    #     JiggleWaves,JiggleForms = kwargs.values()
    #     supA = SuperpositionJiggle(freqsA, magsA, phasesA)
    #     return cls(supA, sample_length=sample_length)





class SingleJiggle(Waveform):
    # """ A simple single trap configuration that is Sinusodally modulated.
    #
    # Attributes
    # ----------
    # Waves : list of :class:`~wavgen.utilities.Wave`
    #     The list of composing pure tones. Each object holds a frequency,
    #     magnitude, and relative phase.
    #
    # Hint
    # ----
    # There are now 3 relevant **amplitudes** here:
    # :meth:`Output Voltage Limit <wavgen.card.Card.setup_channels>`,
    # :attr:`Waveform Amplitude <wavgen.waveform.Waveform.Amplitude>`, & the
    # :attr:`amplitudes of each pure tone <wavgen.utilities.Wave.Magnitude>`
    # composing a superposition. Each one is expressed as a fraction of the previous.
    #
    # See Also
    # --------
    # """

    def __init__(self, base_freq, mod_freq, mod_amp, mod_form, base_phase=0, mod_phase=0, sample_length=None, amp=1.0):
        """
        Provides several options for defining waveform duration.
        Parameters
        ----------
        base_freq :  int, in units of Hz

        mod_freq : int, in units of Hz

        mod_amp : float, in units of Hz, so the phase modulation amplitude is actually (mod_amp/mod_freq)

        base_phase:  float, optional
            base tone initial phase, defualts to be 0

        sample_length : int, optional
            Length of waveform in samples.

        amp : float, optional
            Amplitude of waveform relative to maximum output voltage.
        """
        self.Mod_form = mod_form
        self.Base_freq = base_freq
        self.Mod_freq = mod_freq
        self.Mod_amp = mod_amp
        self.Base_phase = base_phase
        self.Mod_phase = mod_phase

        ## Find the LeastCommonMultiple ##
        if sample_length is None:
            # sample_length = int(SAMP_FREQ * (2 - len(freqs) % 2)//10E6) * 32 * REPEAT *2 # Jacqie made this edit with 10e6 chosen randomly
            # This edit did not work -- intensity jump seen between repetitions due (probably) to phase mis-match. -ED 2021-07-02

            lcm = inf
            for f in [base_freq, mod_freq]:
                digits = 0
                while f%10 == 0:
                    f = f // 10
                    digits += 1
                lcm = min(digits, lcm)
                """
                + 1
                """
            print(lcm)
            # Leon: this base 10 lcm thing doesn't look like the optimal shortest waveform. Will leave it for now.
            sample_length = (SAMP_FREQ / 10**lcm) * 32 * REPEAT
            print(sample_length)
            while sample_length < 384:
                sample_length += sample_length
            msg = "Waveform will not be an integer # of periods.\nYou may want to calculate a sample length manually"
        if sample_length % 1:
            msgbox(msg, "Warning")
        else:
            sample_length = int(sample_length)


        assert mod_freq >= SAMP_FREQ/sample_length, "Modulation Frequency is below resolution. Increase sample length."
        assert base_freq < SAMP_FREQ / 2, ("Frequency %d must below Nyquist: %d" % (base_freq, SAMP_FREQ / 2))

        ## Initialize ##
        super().__init__(sample_length, amp)

    def compute(self, p, q):
        N = min(DATA_MAX, self.SampleLength - p*DATA_MAX)
        waveform = np.zeros(N, dtype=float)

        f0 = self.Base_freq / SAMP_FREQ # Cycles/Sample
        phi0 = self.Base_phase
        mag0 = 1

        f1 = self.Mod_freq / SAMP_FREQ # Cycles/Sample
        phi1 = self.Mod_phase

        mag1 = self.Mod_amp/self.Mod_freq
        # print('________________________')
        # print([self.Mod_amp,self.Mod_freq])
        # print('________________________')
        # # print([f0,mag0,phi0,f1,mag1,phi1])

        mod_form = self.Mod_form

        ## Compute the Wave ##
        for i in range(N):
            n = i + p*DATA_MAX
            if mod_form == "Sine":
                waveform[i] += mag0 * sin(2*pi*f0 * n + phi0 + mag1* sin(2*pi*f1 * n + phi1))
            if mod_form == "Toggle":
                waveform[i] += mag0 * sin(2*pi*f0 * n + phi0 + np.pi/2 *mag1* signal.sawtooth(2*pi*f1 * n, 0.5))

        ## Send the results to Parent ##
        # print(f'max = {max(waveform.max(), abs(waveform.min()))}')
        q.put((p, waveform, max(waveform.max(), abs(waveform.min()))))
        # return max(waveform.max(), abs(waveform.min()))


    def config_dset(self, dset):
        ## Contents ##
        dset.attrs.create('base_freqs', data=np.array([self.Base_freq]))
        dset.attrs.create('mod_freqs', data=np.array([self.Mod_freq]))
        dset.attrs.create('mod_amps', data=np.array([self.Mod_amp]))
        dset.attrs.create('base_phase', data=np.array([self.Base_phase]))
        dset.attrs.create('mod_phase', data=np.array([self.Mod_freq]))
        ## Table of Contents ##
        dset.attrs.create('keys', data=['base_freqs','mod_freqs','mod_amps','base_phase','mod_phase', 'sample_length'])

        return dset


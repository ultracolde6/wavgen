import wavgen

if __name__=='__main__':
    A = wavgen.waveform.LinearTest()
    dwCard = wavgen.Card()
    dwCard.setup_channels(amplitude = 350, use_filter=False)
    dwCard.load_waveforms(A, mode='replay')
    dwCard.wiggle_output(duration=0)
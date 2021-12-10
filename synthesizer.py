from typing import Dict
import pynput;
import numpy as np;
import tkinter as tk;
import sounddevice as sd
import math as Math

class Synthesizer:

    track_duration : float = 20.0 #in seconds
    samplerate : int = 22050
    min_note : float = 1/2  #min 8th notes, 4/4 time signature from 16th notes.
    segment_size : int = int(samplerate*min_note)  #16th note to wave values
    # track_height : int = 24   #daefault 2 octaves
    # base_freq = 440.0
    base_freqs = [16.35,17.32,18.35,19.45,20.60,21.83,23.12,24.50,25.96,27.50,29.14,30.87]  #from c0 to b0
    base_note_names = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B",]
    cur_note_names = []
    note_chart : list[float]
    lower_octave : int
    upper_octave : int
    track_wave : list[float]
    track_notes : dict = {}     #notes stored as (time,pitch) = duration, where time is [noteseg_duration * time] seconds into the track. pitch is relative to base octave(base set of 12 notes, in which the first note is C0(16.35 hz). duration is in seconds)
    volume : float = 40


    #would be cool to have a note chart that correlated to row within the chart, but also self generated. 

    def __init__(self,lower:int,upper:int,duration,rate = 44100, min_note_length : float = 1/2):
        self.lower_octave = lower
        self.upper_octave = upper
        self.samplerate = rate
        self.track_duration = duration
        self.min_note = min_note_length
        self.segment_size = self.samplerate*self.min_note

        self.update_notechart(self.lower_octave,self.upper_octave)

    def update_trackwave(self):#,segments:Dict, duration,rate,seg_dur):
        
        self.track_wave = []
            #populate with 0.
        for n in range(int(self.samplerate*self.track_duration)):
            self.track_wave.append(0.0)
        
        self.track_wave = np.sin(self.track_wave)
        
        #for notes i'll need to have duration, frequence and position. 
        for key in self.track_notes:
            base = int(self.segment_size*key[0])    #beginning of note in trackwave
            length = int((self.track_notes[key]-.01)*self.samplerate) #length of note
            center = length/2
            for j in range(base,base+length):
                self.track_wave[j] += min(((center-abs(center-(j-base)))/200),1) * Math.sin(j/((self.samplerate/(2*np.pi))/self.note_chart[key[1]]))
        
        if(len(self.track_notes) > 0):
            self.track_wave = self.track_wave*(self.volume/100)/np.max(self.track_wave)
        #else nothing
    def update_octaves(self, l_oct, u_oct):
        self.lower_octave = l_oct
        self.upper_octave = u_oct

        self.update_notechart(l_oct,u_oct)
        self.clear_notes()

        pass

    def update_notechart(self, b_oct:int,p_oct:int):
        #updates note_chart with new bounds. both sides inclusive, so a single octave note chart would be x,x. 2 would be x,x+1
        self.note_chart = []
        for i in range(b_oct,p_oct+1):
            for c,j in enumerate(self.base_freqs):
                self.note_chart.append(j*Math.pow(2,i))  #generates note frequencies using base_freq*2^i. (A4 = 440.0 hz, A5 = 880.0 hz, A6 = 1760.0 hz)
                self.cur_note_names.append(self.base_note_names[c]+str(i))

    def play_track(self):
        sd.play(self.track_wave,self.samplerate)
    
    def stop_track(self):
        sd.stop()
    
    def note_exists(self, key : tuple):
        return key in self.track_notes
    
    def set_note(self,key:tuple,dur:float):
        #sets note at key to duration.
        self.track_notes[key] = dur
        #maybe update here? 
    def delete_note(self,key:tuple):
        del self.track_notes[key]
    
    def clear_notes(self):
        self.track_notes.clear()
        self.track_wave = []

    def get_note_dur(self,key:tuple)->float:
        return 0.0 if not key in self.track_notes else self.track_notes[key]
    
    def set_volume(self,vol):
        self.volume = int(vol)
    # def main(self):

    #     # samplerate = 22050  #rate of wave updates.
    #     # track_duration = 20.0 #in seconds
    #     # segment_size = samplerate*self.min_note    
        
    #     # track_width = samplerate*track_duration/segment_size    #in 16th notes.
    #     # track_segments = {} #thisll be a dict of tuples (x,y) : duration
    #     # track_wave = []
    #     self.track_notes[(0,3)] = .5   #note at 0(time),0(lowest note of lowest octave), .25 duration in uhh, seconds?
    #     self.track_notes[(8,5)] = .25
    #     self.track_notes[(16,7)] = .5   #note at 0(time),0(lowest note of lowest octave), .25 duration in uhh, seconds?
    #     self.track_notes[(24,9)] = .25
    #     self.update_trackwave()#track_segments,track_duration,samplerate)
    #     sd.play(self.track_wave)
    #     # for i in track_width:   #samplerate*track_duration:
    #     #     track_segments.append()
    #     #     for j in segment_size:
    #     #         track_wave.append(0.0)
        

    #     window = tk.Tk()
    #     greeting = tk.Label(text="Testing one two.")
    #     greeting.pack()





    #     window.mainloop()

# synth = Synthesizer(2,3,4)

# synth.track_notes[(0,3)] = 1   #note at 0(time),0(lowest note of lowest octave), .25 duration in uhh, seconds?
# synth.track_notes[(8,5)] = .25
# synth.track_notes[(16,7)] = 1   #note at 0(time),0(lowest note of lowest octave), .25 duration in uhh, seconds?
# synth.track_notes[(24,9)] = .25

# synth.update_trackwave()
# sd.play(synth.track_wave)
# sd.wait()
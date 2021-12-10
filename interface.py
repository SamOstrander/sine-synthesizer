import tkinter as tk
from tkinter import filedialog
from tkinter.constants import ALL, BOTTOM, END, INSERT, LEFT, N, NE, NW, RIGHT, TOP, X, Y
import tkinter.font as tkFont
from typing import Text
from synthesizer import Synthesizer
import math as Math
#import wave
import soundfile

import csv
#import json


class Interface():
    #object which manages input detection and 
    mouse_position : tuple
    synth : Synthesizer
    canv : tk.Canvas
    
    root : tk.Tk

    #interface widgets
    settings_frame : tk.Frame       #settings frame, top
    track_frame : tk.Frame          #track frame, bottom
    length_frame : tk.Frame
    play_butn : tk.Button           #play track audio button
    stop_butn : tk.Button
    clear_butn : tk.Button          #clear track notes button
    export_butn : tk.Button         #export to wav file button
    vol_slider : tk.Scale           #slider for track volume
    horiz_scroll : tk.Scrollbar     #horizontal scrollbar for track navigation
    vert_scroll : tk.Scrollbar      #vertical scrollbar for track navigation
    duration_label : tk.Label
    duration_box : tk.Entry          #user input for track duration
    
    canv_size : tuple

    bar_number : int    #track bars
    track_width : int   #width of track in pixels   #do i need this value?
    track_height : int  #height of track in pixels
    track_ypos : int    #distance from top of window to top of track space. in pixels
    track_xpos : int    #distance from left side of window to left side of track space. in pixels
    
    #bottom_pad : int = 0       #pad between bottom of track and bottom of canvas.
    bar_height : int            #height of bars of tracks. in pixels
    time_to_pixels : int = 100  #conversion ratio for note length to pixels. in pixels/second
    note_height : int           #height of notes(within track bars). in pixels
    note_pad : int = 2          #padding between note rects and surrounding bars. in pixels
    #noteseg_pad : int = 2      #small gap for the edges of notes. in pixels.
    noteseg_width : int         #min width of a note. in pixels.
    notes : list                #ids for note rects drawn to canvas.
    bars : list                 #ids for track bars drawn to canvas.
    note_names : list           #ids for note names (text) drawn to canvas.
    length_entry : tk.StringVar #str= ''          #track length input (unsanitized)

    view_pos : tuple[int,int] = (0,0) #position of top left corner of view, where 0,0 shows top left of track, and track_size-view_size = bottom right of track.

    note_font : tkFont.Font

    noteseg_dict : dict = dict()    #breaks notes into segments which are used by the ui. key:val =  (seg_id,pitch):(time,pitch), where value tuple functions as a key for track_notes

    selected_note : tuple   #key of selected note. grabbed on keypress while over valid note.
    selected_length : int=0 #could also check against duration/min_note of the note

    def __init__(self, synth:Synthesizer,root:tk.Tk):
        self.root = root
        self.synth = synth

        self.window_size = (800,600)
        self.canv_size = (800,530)  #should work.
        #print(self.canv_size)
        root.geometry(str(self.window_size[0])+'x'+str(self.window_size[1]))

        self.settings_frame = tk.Frame(root)
        self.settings_frame.pack(anchor = tk.N)#side=TOP)
        self.track_frame = tk.Frame(root)
        self.track_frame.pack(fill='both', expand= True, anchor = tk.W)#pack(side=BOTTOM)

        self.canv = tk.Canvas(self.track_frame)#, width=self.canv_size[0], height=self.canv_size[1]-70)
        self.canv.configure(scrollregion=self.canv.bbox("all"))

        self.horiz_scroll = tk.Scrollbar(self.track_frame,orient=tk.HORIZONTAL,command=self.canv.xview)
        self.horiz_scroll.pack(side=BOTTOM,fill= X)
        self.canv.configure(xscrollcommand=self.horiz_scroll.set)

        self.vert_scroll = tk.Scrollbar(self.track_frame,orient=tk.VERTICAL,command=self.canv.yview)
        self.vert_scroll.pack(side=RIGHT,fill= Y)
        self.canv.configure(yscrollcommand=self.vert_scroll.set)

        self.canv.pack(fill='both',expand=True,side=tk.TOP,anchor='nw')

        #frame to hold duration label and entry
        self.length_frame = tk.Frame(self.settings_frame)
        self.length_frame.pack(side='left')
        self.duration_label = tk.Label(self.length_frame,text='Track Length\n(Seconds)')
        self.duration_label.pack(side='top')
        self.length_entry = tk.StringVar()
        self.length_entry.set(str(self.synth.track_duration))

        self.duration_box = tk.Entry(self.length_frame,width=6,justify='left',textvariable=self.length_entry)
        self.duration_box.pack(side='top')

        #button widgets.
        self.play_butn = tk.Button(self.settings_frame,text="Play Track", command=self.play_sound)
        self.play_butn.pack(padx=4,side=tk.LEFT)
        self.stop_butn = tk.Button(self.settings_frame,text="Stop Track", command=self.synth.stop_track)
        self.stop_butn.pack(padx=4,side=tk.LEFT)
        self.clear_butn = tk.Button(self.settings_frame,text="Clear Track", command=self.clear_track)
        self.clear_butn.pack(padx=4,side=tk.LEFT)

        #interfaces directionly with synthesizer.
        self.vol_slider = tk.Scale(self.settings_frame,from_=0,to=100,orient=tk.HORIZONTAL,showvalue=0,label="Volume",command=synth.set_volume)
        self.vol_slider.set(synth.volume)   #set current position to synth volume.
        self.vol_slider.pack(padx=4,side=tk.RIGHT)

        self.export_butn = tk.Button(self.settings_frame,text="Export WAV",command=self.export_track)
        self.export_butn.pack(padx=4,side=tk.RIGHT)

        
        self.bar_number = (synth.upper_octave-synth.lower_octave+1)*12

        self.track_width = synth.track_duration*self.time_to_pixels

        self.track_ypos = 20    #makes space for note_times at the top of canvas.
        self.track_xpos = 30    #makes space for note_names on left of canvas.

        self.bar_height = int((600-self.track_ypos)/24)   #int((self.canv_size[1] - self.track_ypos - self.bottom_pad) / self.bar_number)    #calc bar height.
        self.note_height = self.bar_height
        self.noteseg_width = self.synth.min_note*self.time_to_pixels    #trying a float#int(self.synth.min_note*self.time_to_pixels)
        
        self.track_height = self.bar_number*self.bar_height
        
        self.notes = list()
        self.bars = list()
        self.note_names = list()
        self.note_times = list()

        self.note_font = tkFont.Font(family="Times",size=-self.bar_height)
        self.track_frame.bind('<Configure>',self.conf)
        self.canv.bind('<B1-Motion>',self.lmb_dragged)
        self.canv.bind('<ButtonPress-1>',self.lmb_press)
        self.canv.bind('<ButtonPress-3>',self.rmb_pressed)
        self.canv.bind('<B3-Motion>',self.rmb_dragged)


        #dev tool for creating demo songs
        #self.root.bind('<Down>',self.export_song)
        #self.root.bind('<Up>',self.import_song)

        self.vert_scroll.bind_all('<MouseWheel>', self.on_vscroll)
        self.horiz_scroll.bind_all('<Shift-MouseWheel>',self.on_hscroll)

        self.duration_box.bind('<KeyRelease>',self.set_tracklength)
        self.duration_box.icursor(0)
        self.update_canvas()
        
        
    def conf(self,event):
        """resize canvas bbox on window resize"""
        self.canv.configure(scrollregion=self.canv.bbox('all'))


    def play_sound(self):
        """update and play track"""
        self.synth.update_trackwave()
        self.synth.play_track()

    def lmb_dragged(self, event):
        """lmb drag event. handles resizing notes"""
        if (self.selected_length > 0):
            pos = self.global_to_track((event.x,event.y))
            pos = (pos[0],self.selected_note[1])    #act as though the user is dragging over the same row, even if the cursor leaves it.
            dif = pos[0] - self.selected_note[0] + 1
            if (pos[0] < 0 or pos[0] >= self.synth.track_duration/self.synth.min_note or pos[1] <0 or pos[1] > self.track_height/self.bar_height):
                return
            if (dif != self.selected_length):
                #if cursor isn't positioned at the end point of the note, then modify the note.
                if(dif < 1 or (self.is_noteseg_occupied(pos) and dif > self.selected_length)):  #if target position isn't empty, return
                    return
                for n in range(dif-self.selected_length):
                    if self.is_noteseg_occupied((self.selected_note[0]+self.selected_length+n,pos[1])):
                        return
                self.selected_length = dif
                self.set_note(self.selected_note,dif*self.synth.min_note)   #updates note with new duration.
                self.update_notes()
        
    def lmb_press(self,event):
        """lmb press event. handles drawing notes to track"""
        pos = self.global_to_track((event.x,event.y))
        if (pos[0] < 0 or pos[0] >= self.synth.track_duration/self.synth.min_note or pos[1] <0 or pos[1] > self.track_height/self.bar_height):
            return
        if(pos[0] >= 0 and pos[0] < self.synth.track_duration/self.synth.min_note and pos[1] >= 0 and pos[1] < self.bar_number):
            if pos in self.noteseg_dict:
                self.selected_note = self.noteseg_dict[pos]
                self.selected_length = pos[0] - self.selected_note[0] + 1   #+1 includes base noteseg in length
            else:
                self.selected_note = pos
                self.selected_length = 1
            self.set_note(self.selected_note,self.selected_length*self.synth.min_note)
            self.update_notes() #redraws notes.
        #maybe here i would have checks for button clicks? or maybe i have separate widgets to handle the buttons, and they just interface with the interface object.
        else:
            self.selected_length = 0

    def rmb_pressed(self,event):
        """rmb press event. handles note deletion"""
        pos = self.global_to_track((event.x,event.y))
        if pos in self.noteseg_dict:
            self.clear_note(self.noteseg_dict[pos])
            self.update_notes()

    def rmb_dragged(self,event):
        """rmb drag event. handles note deletion"""
        #delete all notes that come in contact with cursor while dragging.
        pos = self.global_to_track((event.x,event.y))
        if pos in self.noteseg_dict:
            self.clear_note(self.noteseg_dict[pos])
            self.update_notes()

    def on_vscroll(self,event):
        """vertical scroll event"""
        if(event.delta > 0 and self.canv.yview()[0] == 0):
            return
        self.canv.yview_scroll(int(-1*(event.delta/120)),'units')
    
    def on_hscroll(self,event):
        """horizontal scroll event"""
        if(event.delta > 0 and self.canv.xview()[0] == 0):
            return
        self.canv.xview_scroll(int(-1*(event.delta/120)),'units')
    
    def set_tracklength(self,event):
        """sets track_duration to length_entry if valid"""
        if(event.keysym == 'Return'):
            string = self.length_entry.get()
            if(string.isdigit() and float(string) > 0):
                self.update_track_duration(Math.ceil(float(string)/self.synth.min_note)*self.synth.min_note) #ceil to highest min note.
                self.root.focus_set()

    def update_track_duration(self,dur):
        """resizes track_duration and handles cutoff note deletion"""
        self.synth.track_duration = dur
        self.track_width = self.synth.track_duration*self.time_to_pixels
        #need to remove notes that extend past the new cutoff. 
        cutoff = int(dur/self.synth.min_note)
        for n in list(self.noteseg_dict.keys()):
            if n[0] >= cutoff and n in self.noteseg_dict:
                key = self.noteseg_dict[n]
                length = int(self.synth.track_notes[key]/self.synth.min_note)
                
                for i in range(length):
                    del self.noteseg_dict[(key[0]+i,key[1])]
                del self.synth.track_notes[key]
            
        self.update_canvas()
    
    def clear_track(self):
        """removes all notes from track + display and stops the audio stream."""
        self.synth.stop_track()
        self.erase_notes()
        self.noteseg_dict = {}
        self.synth.clear_notes()
    
    def export_track(self):
        """exports track as a wav file"""
        
            #bugfix for if the track is exported before it's played. (track_wave generated upon play)
        self.synth.update_trackwave()

        dir = filedialog.asksaveasfilename(defaultextension=".wav",filetypes=[("Wave files", "*.wav")])
        soundfile.write(dir,self.synth.track_wave,self.synth.samplerate)

    def erase_bars(self):
        """clears all bars from canvas"""
        for n in self.bars:
            self.canv.delete(n)
        self.bars.clear()

    def erase_notes(self):
        """clears all notes from canvas"""
        for n in self.notes:
            self.canv.delete(n)
        self.notes.clear()
    
    def draw_bars(self):
        """draws track bars to canvas"""
        for i in range(1,self.bar_number+1):
            self.bars.append(self.canv.create_line(self.track_xpos,self.track_ypos+i*self.bar_height,self.track_xpos + self.track_width,self.track_ypos+i*self.bar_height,fill='#000000')) #create lines from notes
        #i'll just but vert bars here.
        for i in range(int(self.synth.track_duration/self.synth.min_note)):
            col = '#000000' if i*self.synth.min_note%1 == 0 else '#9B9B9B'
            self.bars.append(self.canv.create_line(self.track_xpos+i*self.synth.min_note*self.time_to_pixels,self.track_ypos,(self.track_xpos+i*self.synth.min_note*self.time_to_pixels,self.track_ypos+self.track_height),width=1,fill=col))

        #draw a final, thick line to cap off the track.
        self.bars.append(self.canv.create_line(self.track_xpos+self.track_width,self.track_ypos,self.track_xpos+self.track_width,self.track_ypos+self.track_height+1,width=3,fill="#000000"))#draw right line, this is so it's drawn atop the vertical lines.
        self.bars.append(self.canv.create_line(self.track_xpos,self.track_ypos,self.track_xpos + self.track_width,self.track_ypos,fill='#000000')) #draw top line
    
    def draw_notes(self):
        """draws notes to canvas"""
        for n in self.synth.track_notes:
            tl_rel = (self.note_pad,self.note_pad)  #slight offset from top and bottom, so the note isn't ontop of the lines/other notes.
            br_rel = (self.synth.track_notes[n]*self.time_to_pixels,self.note_height)   #relative position of bottom right of note.
            off = (self.track_xpos+n[0]*self.synth.min_note*self.time_to_pixels,self.track_ypos+n[1]*self.bar_height)   #offset of note.
            
            self.notes.append(self.canv.create_rectangle(tl_rel[0]+off[0],tl_rel[1]+off[1],br_rel[0] + off[0]-2,br_rel[1] + off[1]-2,fill='#000000'))

    def draw_note_names(self):
        """draws note names to canvas"""
        text_hheight = self.bar_height/2   #in pixels.
        
        for n,v in enumerate(self.synth.cur_note_names):
            self.note_names.append(self.canv.create_text(self.track_xpos-3,self.track_ypos+n*self.bar_height+text_hheight,text=v,anchor="e"))
        
    def erase_note_names(self):
        """clears all note names from canvas"""
        for n in self.note_names:
            self.canv.delete(n)
        self.note_names.clear()
        
    def draw_note_times(self):
        """draw second indicators to canvas"""
        #draws current time along columns at each second increment.
        text_pad = 2#self.synth.min_note*self.time_to_pixels/2
        for i in range(int(self.synth.track_duration)):
            self.note_times.append(self.canv.create_text(self.track_xpos+i*self.time_to_pixels+text_pad,self.track_ypos-8,text=i))#,anchor="n"))
    
    def erase_note_times(self):
        """clears all note times from canvas"""
        for n in self.note_times:
            self.canv.delete(n)
        self.note_times.clear()

    def update_bars(self):
        """clears and then redraws bars"""
        self.erase_bars()
        self.draw_bars()

    def update_notes(self):
        """clears and then redraws notes"""
        self.erase_notes()
        self.draw_notes()
    
    def update_note_times(self):
        """clears and then redraws note times"""
        self.erase_note_times()
        self.draw_note_times()
    
    def update_note_names(self):
        """clears and then redraws note names"""
        self.erase_note_names()
        self.draw_note_names()

    def update_canvas(self):
        """full canvas clear and redraw"""
        self.update_bars()
        self.update_notes()
        self.update_note_names()
        self.update_note_times()
        self.canv.configure(scrollregion=self.canv.bbox("all"))
        
        self.canv.pack(fill='both', expand=1)
    
    def global_to_track(self,glob:tuple):
        """converts position within canvas to position within track"""
        bbox_width = self.canv.bbox(ALL)[2]-self.canv.bbox(ALL)[0]
        bbox_height = self.canv.bbox(ALL)[3]-self.canv.bbox(ALL)[1]
        
        x = (glob[0] - self.track_xpos+self.canv.xview()[0]*bbox_width)/self.noteseg_width
        y = (glob[1] - self.track_ypos+self.canv.yview()[0]*bbox_height)/self.bar_height

            #bugfix. int was flooring negative decimal to 0
        x = -1 if x < 0 else int(x)
        y = -1 if y < 0 else int(y)
        return (x,y)
        

    def is_noteseg_occupied(self,key:tuple)->bool:
        """returns if noteseg occupied"""
        return key in self.noteseg_dict

    def set_note(self,key:tuple,val:float):
        """updates segment dict with new note and then sets synth.track_notes."""
        if key in self.noteseg_dict:
            for n in range(int(self.synth.get_note_dur(key)/self.synth.min_note)):
                #remove all the previous notes from noteseg
                del self.noteseg_dict[(key[0]+n,key[1])]    #i shouldn't need to confirm that the key:val pair already exists.
        self.synth.set_note(key, val)
        for n in range(int(val/self.synth.min_note)):
            self.noteseg_dict[(key[0]+n,key[1])] = key

    def clear_note(self,key:tuple):
        """clears notes from segment dict and then from synth.track_notes."""
            #maybe convert to a try except deal.
        for n in range(int(self.synth.get_note_dur(key)/self.synth.min_note)):
            #remove all the previous notes from noteseg
            subkey = (key[0]+n,key[1])
            if subkey in self.noteseg_dict:
                del self.noteseg_dict[subkey]    #i shouldn't need to confirm that the key:val pair already exists.
        self.synth.delete_note(key)

    def add_song(self,notes:dict):
        for n in notes:
            self.set_note(n,notes[n])
        self.update_canvas()
    

    #dev tool for creating demo song
    """def export_song(self,event):
        print("exported")
        f = csv.writer(open("song.csv", "w",newline=''))
        for key, val in self.synth.track_notes.items():
            f.writerow([key[0],key[1], val])    #break tuple into 2 ints.
    
    def import_song(self,event):
        print("imported")
        f = csv.reader(open("song.csv", "r",newline=''))
        for row in f:
            print(row)
            self.set_note((int(row[0]),int(row[1])),float(row[2]))
        self.update_canvas()"""

def main():
    window = tk.Tk() #base widget
    window.title("Sine Synthesizer")
    interface = Interface(Synthesizer(2,7,15,min_note_length=1/8),window)

    #demo song
    song = {
    (0,16):1.0,
    (0,21):1.0,
    (16,20):1.0,
    (16,15):1.0,
    (32,19):1.0,
    (32,14):1.0,
    (48,16):1.0,
    (48,11):1.0,
    (56,16):0.25,
    (56,11):0.25,
    (60,19):0.25,
    (62,20):0.25,
    (58,11):0.25,
    (58,16):0.25,
    (60,14):0.25,
    (62,15):0.25,
    (64,16):1.0,
    (64,21):1.0,
    (80,15):1.0,
    (80,20):1.0,
    (96,14):1.0,
    (96,19):1.0,
    (112,11):1.0,
    (112,16):1.0}
    
    interface.add_song(song)
    
    window.mainloop()


if __name__ == "__main__":
    main()
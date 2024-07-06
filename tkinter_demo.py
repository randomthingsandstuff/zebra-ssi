from tkinter import *
from tkinter import font
from tkinter import ttk
from PIL import Image, ImageTk
from ssi_barcode import ssi
import customtkinter as ctk
import threading
import time
import serial
import io

mtx = threading.Lock()
value = None

class ReadOnlyTextbox(ctk.CTkTextbox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure(state=DISABLED)

    def update(self, text):
        self.configure(state=NORMAL)
        self.delete("0.0", "end")
        self.insert("end", text)
        self.configure(state=DISABLED)


class CounterThread(threading.Thread):

    def run(self):
        global value
        global root
        while True:
            time.sleep(1)
            mtx.acquire()
            print("acquired mutex")
            value += 1
            mtx.release()
            root.event_generate('<<ValueEvent>>')


class BarcodeThread(threading.Thread):
    def run(self):
        global value
        global root

        with serial.Serial('/dev/ttyACM0', 9600, rtscts=True) as ser:
            scanner = ssi.SSITransport(ser)
            for packet in scanner.run():
                mtx.acquire()
                value = packet
                mtx.release()
                root.event_generate('<<ValueEvent>>')




def update_value(event):
    v = None
    mtx.acquire()
    v = value
    mtx.release()
    if v is not None:
        textbox.update(value.text_dump())
        if value.decode:
            image = Image.open(io.BytesIO(value.decode.image_data))
            width, height = image.size
            photo_image = ctk.CTkImage(light_image=image, dark_image=image, size=(width, height))
            img_label.configure(image=photo_image)
            img_label.image = photo_image
        else:
            img_label.configure(image=None)
            img_label.image = None

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

x = BarcodeThread()

x.start()

root = ctk.CTk()
root.geometry("640x480")

root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0, weight=1)

frm = ctk.CTkFrame(root)
frm.grid(row=0, column=0, sticky="nsew")
frm.grid_columnconfigure(0, weight=1)
frm.grid_rowconfigure(0, weight=1)
label = ctk.CTkLabel(frm, text=value)
root.bind('<<ValueEvent>>', update_value)
label.grid(column=0, row=0)
textbox = ReadOnlyTextbox(frm)
textbox_font = ctk.CTkFont(family="monospace")
textbox.grid(column=0, row=0, sticky='NESW')
textbox.configure(state=DISABLED, font=textbox_font)
img_frame = ctk.CTkFrame(frm)
img_frame.grid()
img_frame.grid(column=0, row=1)
img_label = ctk.CTkLabel(img_frame, text="")
img_label.grid(column=0, row=0, sticky="NESW")
ctk.CTkButton(frm, text="Quit", command=root.destroy).grid(column=0, row=2)
root.mainloop()

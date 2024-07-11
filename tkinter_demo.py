import tkinter as tk
from tkinter import font as tkfont
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
        self.configure(state="disabled")

    def update(self, text):
        self.configure(state="normal")
        self.delete("0.0", "end")
        self.insert("end", text)
        self.configure(state="disabled")


class CounterThread(threading.Thread):
    def __init__(self, root):
        super().__init__()
        self.root = root

    def run(self):
        global value
        while True:
            time.sleep(1)
            mtx.acquire()
            value += 1
            mtx.release()
            self.root.event_generate("<<ValueEvent>>")


class BarcodeThread(threading.Thread):
    def __init__(self, root):
        super().__init__()
        self.root = root

    def run(self):
        global value
        with serial.Serial('/dev/ttyACM0', 9600, rtscts=True) as ser:
            scanner = ssi.SSITransport(ser)
            for packet in scanner.run():
                mtx.acquire()
                value = packet
                mtx.release()
                self.root.event_generate("<<ValueEvent>>")


class GUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("640x480")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frm = ctk.CTkFrame(self)
        self.frm.grid(row=0, column=0, sticky="nsew")
        self.frm.grid_columnconfigure(0, weight=1)
        self.frm.grid_rowconfigure(0, weight=1)

        self.label = ctk.CTkLabel(self.frm, text="")
        self.label.grid(column=0, row=0)

        self.textbox = ReadOnlyTextbox(self.frm)
        self.textbox_font = ctk.CTkFont(family="monospace")
        self.textbox.grid(column=0, row=0, sticky='NESW')
        self.textbox.configure(state="disabled", font=self.textbox_font)

        self.img_frame = ctk.CTkFrame(self.frm)
        self.img_frame.grid(column=0, row=1)
        self.img_label = ctk.CTkLabel(self.img_frame, text="")
        self.img_label.grid(column=0, row=0, sticky="NESW")

        self.button = ctk.CTkButton(self.frm, text="Quit", command=self.destroy)
        self.button.grid(column=0, row=2)

        self.bind("<<ValueEvent>>", self.update_value)

    def update_value(self, event):
        global value
        mtx.acquire()
        v = value
        mtx.release()
        if v is not None:
            self.textbox.update(v.text_dump())
            if v.decode:
                image = Image.open(io.BytesIO(v.decode.image_data))
                width, height = image.size
                photo_image = ctk.CTkImage(light_image=image, dark_image=image, size=(width, height))
                self.img_label.configure(image=photo_image)
                self.img_label.image = photo_image
            else:
                self.img_label.configure(image=None)
                self.img_label.image = None


def main():
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    gui = GUI()
    barcode_thread = BarcodeThread(gui)
    barcode_thread.start()
    gui.mainloop()


if __name__ == "__main__":
    main()


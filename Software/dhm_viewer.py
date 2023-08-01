#!/usr/bin/env python3

from gui.main_window import start_ui, mainloop
from visualizer.empty_visualizer import EmptyVisualizer
from visualizer import activate

# Open window
launcher, main_window = start_ui()

visualizer = EmptyVisualizer(main_window)
activate(visualizer)
mainloop()
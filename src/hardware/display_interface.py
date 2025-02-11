# src/hardware/display_interface.py

from abc import ABC, abstractmethod

class DisplayInterface(ABC):
    @abstractmethod
    def init_display(self):
        pass

    @abstractmethod
    def update(self, board_state):
        pass

    @abstractmethod
    def cleanup(self):
        pass
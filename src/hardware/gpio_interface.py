from abc import ABC, abstractmethod

class GPIOInterface(ABC):
    @abstractmethod
    def setup(self):
        """Initialize GPIO pins and setup event detection"""
        pass

    @abstractmethod
    def cleanup(self):
        """Clean up GPIO resources when no longer needed"""
        pass
    
    @abstractmethod
    def get_button_states(self):
        """
        Returns a dictionary with the current state of all buttons
        
        Returns:
            dict: Dictionary with button states (up, down, left, right, fire, mode)
        """
        pass
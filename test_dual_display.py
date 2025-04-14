import tkinter as tk
import time
import random
import numpy as np

def create_mock_board():
    """Create a mock board for testing"""
    board = np.zeros((10, 10), dtype=int)
    
    # Add some ships (value 1)
    for i in range(5):
        x, y = random.randint(0, 9), random.randint(0, 9)
        length = random.randint(2, 5)
        horizontal = random.choice([True, False])
        
        for j in range(length):
            if horizontal and y + j < 10:
                board[x, y + j] = 1
            elif not horizontal and x + j < 10:
                board[x + j, y] = 1
    
    # Add some hits (value 2)
    for _ in range(10):
        x, y = random.randint(0, 9), random.randint(0, 9)
        if board[x, y] == 1:
            board[x, y] = 2
    
    # Add some misses (value 3)
    for _ in range(15):
        x, y = random.randint(0, 9), random.randint(0, 9)
        if board[x, y] == 0:
            board[x, y] = 3
    
    return board

def main():
    """Test the secondary display with a mock game board"""
    print("Testing HDMI-1 monitor display (1024x600)...")
    print("This should open a window on your small monitor (HDMI-1)")
    
    # Create main window
    root = tk.Tk()
    root.title("Pao'er Ship - HDMI-1 Test")
    
    # Position on HDMI-1 (small monitor)
    # For Raspberry Pi with HDMI-1 as small screen
    root.geometry("1024x600+0+0")
    
    # Create canvas for drawing
    canvas = tk.Canvas(root, width=1024, height=600, bg="#141420")
    canvas.pack(fill=tk.BOTH, expand=True)
    
    # Add title
    title_label = tk.Label(
        root, 
        text="Pao'er Ship - Game Board Display",
        font=("Arial", 18, "bold"),
        bg="#141420",
        fg="white"
    )
    title_label.place(relx=0.5, y=30, anchor="center")
    
    # Add status message that will update
    status_label = tk.Label(
        root, 
        text="Ready to test...",
        font=("Arial", 14),
        bg="#141420",
        fg="#80C0FF"
    )
    status_label.place(relx=0.5, y=570, anchor="center")
    
    # Colors for cells
    colors = {
        0: "#323232",  # Empty - Dark Gray
        1: "#00FF00",  # Ship - Green
        2: "#FF0000",  # Hit - Red
        3: "#0000FF",  # Miss - Blue
    }
    
    # Create initial board
    current_board = create_mock_board()
    
    def draw_board(board, message="Game Board Display"):
        """Draw the game board on the canvas"""
        # Clear canvas
        canvas.delete("all")
        
        # Update status message
        status_label.config(text=message)
        
        # Add some text explaining the display
        canvas.create_text(
            512, 70,
            text="Game board display on HDMI-1 monitor",
            fill="white",
            font=("Arial", 14)
        )
        
        # Calculate optimal cell size for small screen
        cell_size = 40
        grid_offset_x = (1024 - (cell_size * 10)) // 2
        grid_offset_y = (600 - (cell_size * 10)) // 2 + 20  # Add some space for title
        
        # Draw column labels (A-J)
        for x in range(10):
            canvas.create_text(
                grid_offset_x + x * cell_size + cell_size // 2,
                grid_offset_y - 20,
                text=chr(65 + x),
                fill="white",
                font=("Arial", 14)
            )
        
        # Draw row labels (1-10)
        for y in range(10):
            canvas.create_text(
                grid_offset_x - 20,
                grid_offset_y + y * cell_size + cell_size // 2,
                text=str(y + 1),
                fill="white",
                font=("Arial", 14)
            )
        
        # Draw grid cells
        for y in range(10):
            for x in range(10):
                cell_value = board[y][x]
                color = colors.get(cell_value, "#808080")  # Fallback to gray if invalid value
                
                cell_x = x * cell_size + grid_offset_x
                cell_y = y * cell_size + grid_offset_y
                
                # Draw cell
                canvas.create_rectangle(
                    cell_x, cell_y,
                    cell_x + cell_size - 2,
                    cell_y + cell_size - 2,
                    fill=color,
                    outline="#646464",
                    width=1
                )
                
                # Draw hit/miss markers
                if board[y][x] == 2:  # Hit
                    # Draw X for hit
                    canvas.create_line(
                        cell_x + 5, cell_y + 5,
                        cell_x + cell_size - 7, cell_y + cell_size - 7,
                        fill="white", width=2
                    )
                    canvas.create_line(
                        cell_x + cell_size - 7, cell_y + 5,
                        cell_x + 5, cell_y + cell_size - 7,
                        fill="white", width=2
                    )
                elif board[y][x] == 3:  # Miss
                    # Draw O for miss
                    canvas.create_oval(
                        cell_x + 5, cell_y + 5,
                        cell_x + cell_size - 7, cell_y + cell_size - 7,
                        outline="white", width=2
                    )
    
    # Function to update the board periodically
    def update_board():
        nonlocal current_board
        # Create a new random board
        current_board = create_mock_board()
        # Draw the updated board
        draw_board(current_board, f"Board updated at {time.strftime('%H:%M:%S')}")
        # Schedule the next update
        root.after(3000, update_board)  # Update every 3 seconds
    
    # Initial draw
    draw_board(current_board, "Initial board")
    
    # Schedule first update
    root.after(3000, update_board)
    
    # Start the main loop
    root.mainloop()

if __name__ == "__main__":
    main()
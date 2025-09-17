import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import re

# Main application class
class EncodingApp:
    def __init__(self, root):
        """
        Initialize the application.
        - Sets up the main window.
        - Creates frames for input, buttons, and the plot.
        - Initializes UI components.
        """
        self.root = root
        self.root.title("Digital-to-Digital Encoding Schemes")
        self.root.geometry("1000x750")

        # --- State Variables ---
        self.buttons = {}
        self.active_button = None
        # For AMI, B8ZS, HDB3: tracks the polarity of the last '1' bit (+1 or -1)
        self.last_pulse_polarity = -1 

        # --- Main Layout Frames ---
        # Top frame for input field
        input_frame = tk.Frame(root, pady=10)
        input_frame.pack(fill=tk.X)

        # Middle frame for encoding buttons
        button_frame = tk.Frame(root, pady=10)
        button_frame.pack(fill=tk.X)
        
        # Bottom frame for the plot
        self.plot_frame = tk.Frame(root, padx=10, pady=10)
        self.plot_frame.pack(fill=tk.BOTH, expand=True)

        # --- UI Components ---
        # Input section
        tk.Label(input_frame, text="Enter Binary String:", font=("Arial", 12)).pack(side=tk.LEFT, padx=(20, 10))
        self.binary_entry = tk.Entry(input_frame, width=50, font=("Arial", 12))
        self.binary_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 20))
        self.binary_entry.insert(0, "0100000000110") # Default value for demonstration

        # Buttons section
        encoding_methods = [
            "Unipolar", "NRZ-L", "NRZ-I", "RZ", "Manchester", 
            "Differential Manchester", "AMI", "B8ZS", "HDB3"
        ]
        
        # Create 9 buttons in a 2x5 grid layout for better spacing
        for i, method in enumerate(encoding_methods):
            btn = tk.Button(
                button_frame,
                text=method,
                bg="black",
                fg="white",
                font=("Arial", 10, "bold"),
                width=20,
                command=lambda m=method: self.plot_encoding(m)
            )
            # Arrange buttons in a grid
            row = i // 5
            col = i % 5
            btn.grid(row=row, column=col, padx=5, pady=5, sticky='ew')
            self.buttons[method] = btn

        # Configure grid columns to be of equal weight
        for i in range(5):
            button_frame.grid_columnconfigure(i, weight=1)

        # Center the grid of buttons
        button_frame.pack(anchor='n')


        # Matplotlib plot section
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Plot the default value on startup
        self.plot_encoding("Unipolar")

    def validate_input(self, binary_string):
        """
        Validates if the input string contains only '0's and '1's.
        Shows an error message if invalid.
        """
        if not re.match("^[01]+$", binary_string):
            messagebox.showerror("Invalid Input", "Please enter a valid binary string (only '0's and '1's).")
            return False
        return True

    def update_button_styles(self, active_method):
        """
        Updates the button colors. The active button turns red, others turn black.
        """
        if self.active_button:
            self.active_button.config(bg="black", fg="white")
        
        self.active_button = self.buttons[active_method]
        self.active_button.config(bg="red", fg="white")

    def plot_waveform(self, x, y, title):
        """
        Clears the previous plot and draws the new waveform.
        """
        self.ax.clear()
        # Use 'steps-pre' for a clean digital signal look
        self.ax.step(x, y, where='post', color='blue', linewidth=2)
        
        # Add horizontal lines for levels and bit boundaries
        self.ax.axhline(0, color='black', linewidth=0.5, linestyle='--')
        for i in range(len(self.binary_entry.get()) + 1):
            self.ax.axvline(i, color='gray', linestyle=':', linewidth=0.5)

        self.ax.set_title(title, fontsize=14, fontweight='bold')
        self.ax.set_xlabel("Time (bit intervals)", fontsize=12)
        self.ax.set_ylabel("Voltage Level", fontsize=12)
        
        # Set y-axis limits and ticks for clarity
        max_y = max(abs(val) for val in y) if y else 1
        self.ax.set_ylim(-max_y - 0.5, max_y + 0.5)
        self.ax.set_yticks(sorted(list(set(y))))

        self.ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        self.canvas.draw()

    def plot_encoding(self, method):
        """
        Main function called by buttons. It gets the input, validates it,
        calls the appropriate encoding logic, and plots the result.
        """
        binary_string = self.binary_entry.get()
        if not self.validate_input(binary_string):
            return

        self.update_button_styles(method)
        
        # Reset polarity for schemes that need it
        self.last_pulse_polarity = -1

        # Dictionary mapping method names to their handler functions
        encoding_functions = {
            "Unipolar": self.get_unipolar,
            "NRZ-L": self.get_nrz_l,
            "NRZ-I": self.get_nrz_i,
            "RZ": self.get_rz,
            "Manchester": self.get_manchester,
            "Differential Manchester": self.get_diff_manchester,
            "AMI": self.get_ami,
            "B8ZS": self.get_b8zs,
            "HDB3": self.get_hdb3
        }

        # Call the selected encoding function
        x, y = encoding_functions[method](binary_string)
        
        self.plot_waveform(x, y, f"{method} Encoding")

    # --- ENCODING LOGIC FUNCTIONS ---
    
    def get_unipolar(self, data):
        x, y = [0], [0]
        for i, bit in enumerate(data):
            level = 1 if bit == '1' else 0
            x.extend([i, i + 1])
            y.extend([level, level])
        return x, y

    def get_nrz_l(self, data):
        x, y = [0], [1] # Start at a default level
        for i, bit in enumerate(data):
            level = -1 if bit == '1' else 1
            x.extend([i, i + 1])
            y.extend([level, level])
        return x, y

    def get_nrz_i(self, data):
        x, y = [0], [1] # Start at a positive level
        current_level = 1
        for i, bit in enumerate(data):
            if bit == '1':
                current_level *= -1 # Invert on 1
            x.extend([i, i + 1])
            y.extend([current_level, current_level])
        return x, y

    def get_rz(self, data):
        x, y = [0], [0]
        for i, bit in enumerate(data):
            if bit == '0':
                x.extend([i, i + 1])
                y.extend([0, 0])
            else: # bit == '1'
                x.extend([i, i + 0.5, i + 0.5, i + 1])
                y.extend([1, 1, 0, 0])
        return x, y

    def get_manchester(self, data):
        x, y = [0], [1] # Start level
        for i, bit in enumerate(data):
            if bit == '0': # High-to-low transition
                x.extend([i, i + 0.5, i + 0.5, i + 1])
                y.extend([1, 1, -1, -1])
            else: # Low-to-high transition
                x.extend([i, i + 0.5, i + 0.5, i + 1])
                y.extend([-1, -1, 1, 1])
        return x, y

    def get_diff_manchester(self, data):
        x, y = [0], [1] # Start level
        current_level = 1
        for i, bit in enumerate(data):
            # Transition at the start for '0'
            if bit == '0':
                current_level *= -1
            
            # Mid-bit transition for all bits
            x.extend([i, i + 0.5, i + 0.5, i + 1])
            y.extend([current_level, current_level, -current_level, -current_level])
            
            # Update level for the next bit
            current_level *= -1
        return x, y
        
    def get_ami(self, data, is_scrambled=False):
        x, y = [0], [0]
        # Allow pre-scrambled data with 'V' and 'B' for B8ZS/HDB3
        symbols = data if is_scrambled else [(bit, 'normal') for bit in data]

        for i, (symbol, type) in enumerate(symbols):
            if symbol == '0':
                x.extend([i, i + 1])
                y.extend([0, 0])
            else: # For '1' or substitution symbols
                # 'V' (violation) uses the same polarity, 'B' (bipolar) and '1' alternate
                if type != 'violation': 
                    self.last_pulse_polarity *= -1
                
                x.extend([i, i + 1])
                y.extend([self.last_pulse_polarity, self.last_pulse_polarity])
        return x, y

    def get_b8zs(self, data):
        # B8ZS Substitution: 000V B0VB
        # V = Violation, B = Bipolar
        scrambled_data = []
        i = 0
        while i < len(data):
            if data[i:i+8] == '00000000':
                # Determine polarity for V and B based on the last pulse
                v_polarity = self.last_pulse_polarity
                b_polarity = -self.last_pulse_polarity

                # Replace with pattern. Use custom types to guide AMI logic.
                scrambled_data.extend([('0', 'normal'), ('0', 'normal'), ('0', 'normal')])
                scrambled_data.append(('V', 'violation')) # V has same polarity as last pulse
                scrambled_data.append(('B', 'bipolar')) # B has opposite polarity
                scrambled_data.extend([('0', 'normal')])
                scrambled_data.append(('V', 'violation'))
                scrambled_data.append(('B', 'bipolar'))

                # Update the last pulse polarity after the substitution
                self.last_pulse_polarity = b_polarity
                i += 8
            else:
                bit = data[i]
                scrambled_data.append((bit, 'normal'))
                if bit == '1':
                    self.last_pulse_polarity *= -1
                i += 1
        
        # Reset polarity to plot from the beginning
        self.last_pulse_polarity = -1
        return self.get_ami(scrambled_data, is_scrambled=True)

    def get_hdb3(self, data):
        # HDB3 Substitution: 000V or B00V
        scrambled_data = []
        i = 0
        ones_since_last_sub = 0
        while i < len(data):
            if data[i:i+4] == '0000':
                if ones_since_last_sub % 2 == 0: # Even number of 1s -> B00V
                    scrambled_data.append(('B', 'bipolar'))
                    scrambled_data.extend([('0', 'normal'), ('0', 'normal')])
                    scrambled_data.append(('V', 'violation'))
                    self.last_pulse_polarity *= -1 # V is a violation, so polarity stays same relative to B
                else: # Odd number of 1s -> 000V
                    scrambled_data.extend([('0', 'normal'), ('0', 'normal'), ('0', 'normal')])
                    scrambled_data.append(('V', 'violation'))
                
                ones_since_last_sub = 0 # Reset counter
                i += 4
            else:
                bit = data[i]
                scrambled_data.append((bit, 'normal'))
                if bit == '1':
                    ones_since_last_sub += 1
                    self.last_pulse_polarity *= -1
                i += 1
        
        # Reset polarity and plot the scrambled data
        self.last_pulse_polarity = -1
        return self.get_ami(scrambled_data, is_scrambled=True)

# Main execution block
if __name__ == "__main__":
    root = tk.Tk()
    app = EncodingApp(root)
    root.mainloop()

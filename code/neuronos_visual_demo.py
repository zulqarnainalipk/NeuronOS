import numpy as np
import time
import matplotlib.pyplot as plt
from enum import Enum
from collections import defaultdict

# Simplified versions of NeuronOS components for demonstration
class NPUState(Enum):
    RESTING = 0
    INTEGRATION = 1
    FIRING = 2
    REFRACTORY = 3

class NeuralProcessingUnit:
    def __init__(self, id, threshold=-55.0):
        self.id = id
        self.membrane_potential = -70.0
        self.threshold = threshold
        self.state = NPUState.RESTING
        self.connections = {}
        self.spike_history = []
        
    def add_connection(self, target_id, weight=0.5):
        self.connections[target_id] = weight
        
    def update(self, inputs, current_time):
        # Simple leaky integrate-and-fire model
        self.membrane_potential *= 0.9  # Leak
        
        # Process inputs
        for input_val in inputs:
            self.membrane_potential += input_val
            
        # Check for spike
        if self.membrane_potential >= self.threshold:
            self.state = NPUState.FIRING
            self.spike_history.append(current_time)
            self.membrane_potential = -75.0  # Reset
            self.state = NPUState.REFRACTORY
            return [(target_id, self.connections[target_id]) for target_id in self.connections]
        
        if self.membrane_potential > -65.0:
            self.state = NPUState.INTEGRATION
        else:
            self.state = NPUState.RESTING
            
        return []

class CorticalProcessingModule:
    def __init__(self, id, size=10):
        self.id = id
        self.npus = {}
        self.activity_history = []
        
        # Create NPUs
        for i in range(size):
            npu_id = f"{id}_{i}"
            self.npus[npu_id] = NeuralProcessingUnit(npu_id)
            
        # Connect NPUs (simple random connectivity)
        for source_id, source_npu in self.npus.items():
            for target_id, target_npu in self.npus.items():
                if source_id != target_id and np.random.random() < 0.3:
                    source_npu.add_connection(target_id, np.random.random() * 0.5)
    
    def process(self, inputs, current_time):
        # Distribute inputs to NPUs
        outputs = []
        active_npus = 0
        
        # Process each NPU
        for i, (npu_id, npu) in enumerate(self.npus.items()):
            # Get input for this NPU - Fixed to handle numpy arrays properly
            npu_input = []
            if len(inputs) > 0:
                input_idx = i % len(inputs)
                # Convert numpy array element to scalar if needed
                if isinstance(inputs[input_idx], np.ndarray) and inputs[input_idx].size == 1:
                    npu_input = [float(inputs[input_idx])]
                else:
                    npu_input = [inputs[input_idx]]
            
            # Process and collect outputs
            npu_outputs = npu.update(npu_input, current_time)
            outputs.extend(npu_outputs)
            
            # Track activity
            if npu.state != NPUState.RESTING:
                active_npus += 1
                
        # Record activity level
        activity_level = active_npus / len(self.npus)
        self.activity_history.append((current_time, activity_level))
        
        return outputs, activity_level

class NeuronOSVisualDemo:
    def __init__(self):
        # Create modules
        self.modules = {
            "sensory": CorticalProcessingModule("sensory", 20),
            "processing": CorticalProcessingModule("processing", 30),
            "executive": CorticalProcessingModule("executive", 15)
        }
        
        # System state
        self.current_time = 0
        self.activity_history = defaultdict(list)
        self.spike_counts = defaultdict(list)
        
    def run_simulation(self, duration=100, input_pattern=None):
        """Run a simulation with visualization"""
        print("Starting NeuronOS Visual Demo simulation...")
        
        # Set up visualization
        plt.figure(figsize=(12, 8))
        plt.ion()  # Interactive mode
        
        # Create subplots
        ax1 = plt.subplot(2, 2, 1)  # Activity levels
        ax2 = plt.subplot(2, 2, 2)  # Spike raster plot
        ax3 = plt.subplot(2, 1, 2)  # System diagram
        
        # System diagram (static)
        self._draw_system_diagram(ax3)
        
        # Generate input pattern if not provided
        if input_pattern is None:
            input_pattern = self._generate_input_pattern(duration)
        
        # Run simulation
        for t in range(duration):
            self.current_time = t
            
            # Get input for this time step
            current_input = input_pattern[t % len(input_pattern)]
            
            # Convert to list of floats to avoid numpy array issues
            current_input_list = [float(x) for x in current_input]
            
            # Process through modules
            sensory_output, sensory_activity = self.modules["sensory"].process(current_input_list, t)
            self.activity_history["sensory"].append((t, sensory_activity))
            self.spike_counts["sensory"].append(len(sensory_output))
            
            # Pass to processing module - ensure we're passing simple float values
            processing_input = [float(weight) for _, weight in sensory_output]
            processing_output, processing_activity = self.modules["processing"].process(processing_input, t)
            self.activity_history["processing"].append((t, processing_activity))
            self.spike_counts["processing"].append(len(processing_output))
            
            # Pass to executive module - ensure we're passing simple float values
            executive_input = [float(weight) for _, weight in processing_output]
            executive_output, executive_activity = self.modules["executive"].process(executive_input, t)
            self.activity_history["executive"].append((t, executive_activity))
            self.spike_counts["executive"].append(len(executive_output))
            
            # Update visualization every 5 steps
            if t % 5 == 0 or t == duration - 1:
                self._update_visualization(ax1, ax2, ax3, t)
                plt.pause(0.1)
                
            # Print progress
            if t % 10 == 0:
                print(f"Processing time step {t}/{duration}")
        
        print("Simulation completed!")
        print("Final activity levels:")
        for module_name, history in self.activity_history.items():
            if history:
                print(f"  {module_name}: {history[-1][1]:.2f}")
        
        # Keep plot open
        plt.ioff()
        plt.show()
    
    def _generate_input_pattern(self, duration):
        """Generate a simple input pattern"""
        patterns = []
        
        # Create a few different patterns
        for _ in range(min(5, duration)):
            # Random binary pattern - convert to list of floats immediately
            pattern = (np.random.rand(10) > 0.7).astype(float)
            patterns.append(pattern)
            
        return patterns
    
    def _draw_system_diagram(self, ax):
        """Draw the system diagram"""
        ax.clear()
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 5)
        ax.set_title("NeuronOS System Activity")
        ax.axis('off')
        
        # Draw modules
        module_positions = {
            "sensory": (2, 3.5, 2, 1),
            "processing": (5, 3.5, 2, 1),
            "executive": (8, 3.5, 2, 1)
        }
        
        module_colors = {
            "sensory": "#c6ecc6",
            "processing": "#c6d9ec",
            "executive": "#f2d9e6"
        }
        
        # Draw modules
        for module_name, (x, y, width, height) in module_positions.items():
            color = module_colors[module_name]
            rect = plt.Rectangle((x, y), width, height, facecolor=color, edgecolor='black', alpha=0.8)
            ax.add_patch(rect)
            ax.text(x + width/2, y + height/2, module_name.capitalize(), ha='center', va='center')
        
        # Draw connections
        ax.arrow(4, 3.5 + 0.5, 0.9, 0, head_width=0.1, head_length=0.1, fc='black', ec='black')
        ax.arrow(7, 3.5 + 0.5, 0.9, 0, head_width=0.1, head_length=0.1, fc='black', ec='black')
    
    def _update_visualization(self, ax1, ax2, ax3, current_time):
        """Update the visualization"""
        # Update activity plot
        ax1.clear()
        ax1.set_title("Module Activity Levels")
        ax1.set_xlabel("Time")
        ax1.set_ylabel("Activity Level")
        ax1.set_ylim(0, 1)
        
        for module_name, history in self.activity_history.items():
            if history:
                times, activities = zip(*history)
                ax1.plot(times, activities, label=module_name)
        
        ax1.legend()
        
        # Update spike raster plot
        ax2.clear()
        ax2.set_title("Spike Counts")
        ax2.set_xlabel("Time")
        ax2.set_ylabel("Spikes")
        
        for i, (module_name, counts) in enumerate(self.spike_counts.items()):
            if counts:
                ax2.plot(range(len(counts)), counts, label=module_name)
        
        ax2.legend()
        
        # Update system diagram
        self._draw_system_diagram(ax3)
        
        # Add activity indicators to system diagram
        module_positions = {
            "sensory": (2, 3.5, 2, 1),
            "processing": (5, 3.5, 2, 1),
            "executive": (8, 3.5, 2, 1)
        }
        
        for module_name, history in self.activity_history.items():
            if history:
                # Get current activity
                current_activity = history[-1][1] if history else 0
                
                # Get module position
                x, y, width, height = module_positions[module_name]
                
                # Draw activity indicator
                indicator_height = current_activity * height * 0.8
                indicator = plt.Rectangle((x + width * 0.8, y + height * 0.1), 
                                         width * 0.1, indicator_height, 
                                         facecolor='red', alpha=0.7)
                ax3.add_patch(indicator)
                
                # Add spike count
                if module_name in self.spike_counts and self.spike_counts[module_name]:
                    spike_count = self.spike_counts[module_name][-1]
                    ax3.text(x + width/2, y - 0.2, f"Spikes: {spike_count}", 
                            ha='center', va='center', fontsize=8)

# Run the demo if executed directly
if __name__ == "__main__":
    demo = NeuronOSVisualDemo()
    demo.run_simulation(duration=100)

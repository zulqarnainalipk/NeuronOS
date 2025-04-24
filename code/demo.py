import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.gridspec as gridspec
from matplotlib.patches import Rectangle, Circle, Arrow, FancyArrowPatch, Polygon
from matplotlib.widgets import Button, Slider, RadioButtons
from matplotlib import colors # Import the colors module here
import time
from enum import Enum
from collections import defaultdict
import random

# Set style for better visuals
plt.style.use('dark_background')

# Simplified versions of NeuronOS components for demonstration
class NPUState(Enum):
    RESTING = 0
    INTEGRATION = 1
    FIRING = 2
    REFRACTORY = 3

class NeuralProcessingUnit:
    def __init__(self, id, threshold=-55.0, position=(0, 0)):
        self.id = id
        self.membrane_potential = -70.0
        self.threshold = threshold
        self.state = NPUState.RESTING
        self.connections = {}
        self.spike_history = []
        self.position = position  # For visualization
        self.size = 0.2  # Visual size
        self.color = '#1f77b4'  # Default color
        self.last_update_time = 0
        
    def add_connection(self, target_id, weight=0.5):
        self.connections[target_id] = weight
        
    def update(self, inputs, current_time):
        self.last_update_time = current_time
        
        # Simple leaky integrate-and-fire model
        # More significant leak and integration for faster dynamics
        self.membrane_potential *= 0.85 # Increased Leak
        
        # Process inputs - increased impact and added noise
        input_sum = sum(inputs) + (random.random() - 0.5) * 2 # Add random noise
        self.membrane_potential += input_sum * 3 # Increased input impact
            
        # Check for spike
        if self.membrane_potential >= self.threshold:
            self.state = NPUState.FIRING
            self.spike_history.append(current_time)
            if len(self.spike_history) > 20:  # Keep history limited
                self.spike_history.pop(0)
            self.membrane_potential = -75.0  # Reset potential below resting
            # Immediately enter refractory state after firing
            self.state = NPUState.REFRACTORY 
            return [(target_id, self.connections[target_id]) for target_id in self.connections]
        
        # State transitions after processing input
        if self.state == NPUState.REFRACTORY:
             # Stay in refractory for a short period (e.g., until potential recovers somewhat)
             if self.membrane_potential >= -65.0:
                 self.state = NPUState.INTEGRATION
             # Otherwise remains in REFRACTORY implicitly until potential rises
        elif self.membrane_potential > -65.0: # Integrated enough to be considered active
             self.state = NPUState.INTEGRATION
        else:
             self.state = NPUState.RESTING # Below integration threshold

        return []
        
    def get_color(self):
        # Color based on state - more vibrant colors
        if self.state == NPUState.RESTING:
            return '#1f77b4'  # Blue
        elif self.state == NPUState.INTEGRATION:
            return '#ff7f0e'  # Orange
        elif self.state == NPUState.FIRING:
            return '#d62728'  # Red
        else:  # REFRACTORY
            return '#9467bd'  # Purple

class CorticalProcessingModule:
    def __init__(self, id, size=10, position=(0, 0), radius=1.5):
        self.id = id
        self.npus = {}
        self.activity_history = []
        self.position = position
        self.radius = radius
        self.color = '#2ca02c'  # Default Green (overridden in demo)
        self.connections = []  # For visualization - simplified
        self.activity_level = 0.0 # Track current activity level
        self.outline_patch = None # Matplotlib patch for the outline circle
        
        # Create NPUs in a circular arrangement
        for i in range(size):
            angle = 2 * np.pi * i / size
            npu_x = position[0] + radius * 0.7 * np.cos(angle)
            npu_y = position[1] + radius * 0.7 * np.sin(angle)
            npu_id = f"{id}_{i}"
            self.npus[npu_id] = NeuralProcessingUnit(npu_id, position=(npu_x, npu_y))
            
        # Connect NPUs (simple random connectivity within the module)
        npu_list = list(self.npus.keys())
        for source_id in npu_list:
            for _ in range(int(size * 0.3)): # Attempt to connect ~30% of others
                 target_id = random.choice(npu_list)
                 if source_id != target_id:
                     weight = np.random.random() * 0.5 + 0.5  # Higher weights (0.5-1.0)
                     self.npus[source_id].add_connection(target_id, weight)
                     # Store connection data if needed for drawing internal connections
                     # self.connections.append((source_id, target_id, weight))
    
    def process(self, inputs, current_time):
        outputs = []
        active_npus = 0
        spikes = []
        
        # Prepare inputs mapped to NPUs (e.g., distribute evenly)
        npu_inputs = {npu_id: [] for npu_id in self.npus}
        if inputs:
            for i, input_val in enumerate(inputs):
                # Ensure input_val is a list of numeric values or becomes one
                input_vals_list = []
                if isinstance(input_val, np.ndarray) and input_val.size == 1:
                    input_vals_list = [float(input_val)]
                elif isinstance(input_val, (int, float)):
                    input_vals_list = [float(input_val)]
                elif isinstance(input_val, (list, tuple, np.ndarray)):
                    input_vals_list = [float(x) for x in input_val if isinstance(x, (int, float, np.ndarray))]

                if input_vals_list:
                    target_npu_id = list(self.npus.keys())[i % len(self.npus)]
                    npu_inputs[target_npu_id].extend(input_vals_list)


        # Process each NPU
        current_outputs = {} # Collect outputs temporarily to prevent immediate downstream effect in same time step
        for npu_id, npu in self.npus.items():
            # Ensure npu_inputs[npu_id] is always a list
            npu_output = npu.update(npu_inputs.get(npu_id, []), current_time)
            if npu_output:
                current_outputs[npu_id] = npu_output

            # Track activity
            if npu.state != NPUState.RESTING:
                active_npus += 1
                
            # Track spikes for visualization
            if npu.state == NPUState.FIRING:
                spikes.append(npu_id)
        
        # Flatten outputs from all NPUs in this module
        for npu_id, npu_outputs in current_outputs.items():
             outputs.extend(npu_outputs)

        # Record activity level
        self.activity_level = active_npus / len(self.npus) if self.npus else 0
        self.activity_history.append((current_time, self.activity_level))
        if len(self.activity_history) > 100:  # Keep history limited
            self.activity_history.pop(0)
            
        return outputs, self.activity_level, spikes

class NeuronOSEnhancedDemo:
    def __init__(self):
        # Create modules in a horizontal arrangement
        self.modules = {
            "sensory": CorticalProcessingModule("sensory", 12, position=(3, 5), radius=1.5),
            "processing": CorticalProcessingModule("processing", 16, position=(8, 5), radius=1.8),
            "executive": CorticalProcessingModule("executive", 10, position=(13, 5), radius=1.3)
        }
        
        # Connect modules (using module IDs for flow visualization)
        self.module_connections = [
            ("sensory", "processing"),
            ("processing", "executive")
        ]
        
        # System state
        self.current_time = 0
        self.activity_history = defaultdict(list) # Still store history per module for the graph
        self.active_spikes_data = []  # Data for spikes (module_id, npu_id)
        self.flow_particles_data = [] # Data for flow particles (source, target, progress, speed, size, color)
        
        # Matplotlib artists to update - Initialize as empty or None
        self.npu_patches = {} # Maps npu_id to matplotlib Circle patch
        self.spike_patches = [] # List of matplotlib Circle patches for current spikes/glows
        self.flow_particle_patches = [] # List of (particle_data, particle_circle_patch, glow_circle_patch) tuples
        self.activity_lines = {} # Maps module_name to matplotlib Line2D
        self.info_text_artist = None # Text artist for displaying simulation info
        self.module_outline_patches = {} # Maps module_name to outline patch for activity indication

        # Demo state
        self.running = False
        self.speed = 1.0
        self.input_type = "pattern" # Default input type
        
        # Title and subtitle
        self.title = "NeuronOS: Brain-Inspired AI Architecture"
        self.subtitle = "Information flows through specialized neural modules"
        
        # Module colors - more vibrant
        self.module_colors = {
            "sensory": "#3498db",     # Blue
            "processing": "#2ecc71",  # Green
            "executive": "#e74c3c"    # Red
        }
        
    def generate_input(self):
        """Generate input based on selected type"""
        if self.input_type == "random":
            # Random binary pattern
            return (np.random.rand(10) > 0.6).astype(float) * 3 # Stronger inputs
        elif self.input_type == "pattern":
            # Alternating pattern
            pattern_idx = int(self.current_time * 0.1) % 3 # Use current_time scaled by 0.1
            if pattern_idx == 0:
                return np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0]) * 3
            elif pattern_idx == 1:
                return np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1]) * 3
            else:
                return np.array([1, 1, 0, 0, 1, 1, 0, 0, 1, 1]) * 3
        elif self.input_type == "pulse":
            # Periodic pulse
            if int(self.current_time * self.speed) % 30 < 5: # Make pulse wider and dependent on speed
                return np.ones(10) * 4
            else:
                return np.zeros(10)
        else:  # "none"
            return np.zeros(10)
            
    def update_simulation_data(self):
        """Update the simulation logic, *not* the visuals."""
        if not self.running:
            return
            
        # Update time
        self.current_time += 0.1 * self.speed # Fixed time step

        # Generate input
        current_input = self.generate_input()
        # Ensure current_input is a list of floats for processing
        current_input_list = [float(x) for x in current_input]
        
        # Process through modules
        all_module_outputs = {}
        module_activity_levels = {}
        all_spikes_data = []
        
        # --- Sensory Module ---
        sensory_output, sensory_activity, sensory_spikes = self.modules["sensory"].process(current_input_list, self.current_time)
        all_module_outputs["sensory"] = sensory_output
        module_activity_levels["sensory"] = sensory_activity
        all_spikes_data.extend([("sensory", spike_id) for spike_id in sensory_spikes])

        # --- Processing Module ---
        # Input to processing comes from sensory outputs (weights represent signal strength)
        processing_input = [weight for _, weight in all_module_outputs["sensory"]]
        processing_output, processing_activity, processing_spikes = self.modules["processing"].process(processing_input, self.current_time)
        all_module_outputs["processing"] = processing_output
        module_activity_levels["processing"] = processing_activity
        all_spikes_data.extend([("processing", spike_id) for spike_id in processing_spikes])
        
        # --- Executive Module ---
        # Input to executive comes from processing outputs
        executive_input = [weight for _, weight in all_module_outputs["processing"]]
        executive_output, executive_activity, executive_spikes = self.modules["executive"].process(executive_input, self.current_time)
        all_module_outputs["executive"] = executive_output
        module_activity_levels["executive"] = executive_activity
        all_spikes_data.extend([("executive", spike_id) for spike_id in executive_spikes])
        
        # Update module activity levels (stored in the module objects themselves now)
        for module_name, level in module_activity_levels.items():
             self.modules[module_name].activity_level = level


        # The activity_history is updated within each module's process method.

        self.active_spikes_data = all_spikes_data
        
        # Update flow particles data
        self.update_flow_particles_data()
        

    def update_flow_particles_data(self):
        """Update the data for flow particles (positions, progress)."""
        # Add new particles frequently
        # Increased particle generation chance and density
        if random.random() < 0.8: 
            for source, target in self.module_connections:
                # Add multiple particles per step
                num_particles_to_add = random.randint(1, 3) 
                for _ in range(num_particles_to_add):
                    source_pos = self.modules[source].position
                    target_pos = self.modules[target].position
                    # Start particle near the source module center
                    t = random.random() * 0.1 # Start within first 10% of the path
                    x = source_pos[0] + t * (target_pos[0] - source_pos[0])
                    y = source_pos[1] + t * (target_pos[1] - source_pos[1])
                    self.flow_particles_data.append({
                        'source': source,
                        'target': target,
                        'position': (x, y),
                        'progress': t,
                        'speed': 0.02 + random.random() * 0.02,  # Random speed
                        'size': 0.2 + random.random() * 0.15,     # Random size
                        'color': self.module_colors[source]      # Color based on source module
                    })
        
        # Update existing particles data and remove finished ones
        updated_particles_data = []
        for particle in self.flow_particles_data:
            source_pos = self.modules[particle['source']].position
            target_pos = self.modules[particle['target']].position
            
            # Update progress - speed scales with global speed
            particle['progress'] += particle['speed'] * self.speed 
            
            # If particle reached the end, don't keep it
            if particle['progress'] >= 1.0:
                continue # Don't add to updated_particles_data

            # Update position
            x = source_pos[0] + particle['progress'] * (target_pos[0] - source_pos[0])
            y = source_pos[1] + particle['progress'] * (target_pos[1] - source_pos[1])
            particle['position'] = (x, y)
            
            updated_particles_data.append(particle)
            
        self.flow_particles_data = updated_particles_data

    def setup_visualization(self):
        """Set up the visualization with a completely reimagined layout"""
        self.fig = plt.figure(figsize=(16, 9))  # 16:9 aspect ratio
        
        # Create a custom grid layout
        # Added space for legend/controls on the sides of the bottom row
        gs = gridspec.GridSpec(2, 3, height_ratios=[4, 1], width_ratios=[1, 2, 1]) 
        
        # Main visualization area (spans top row, all columns)
        self.ax_main = plt.subplot(gs[0, :])
        self.ax_main.set_xlim(0, 16)
        self.ax_main.set_ylim(0, 9)
        self.ax_main.axis('off') # Hide axes
        
        # Add title and subtitle (static)
        self.fig.text(0.5, 0.96, self.title,
                      ha='center', va='center', fontsize=24, fontweight='bold', color='white')
        self.fig.text(0.5, 0.92, self.subtitle,
                      ha='center', va='center', fontsize=18, color='white')

        # Add dynamic info text artist
        self.info_text_artist = self.ax_main.text(0.5, 0.98, "", # Position near top center (relative to axes)
                                                    ha='center', va='top', fontsize=12, color='white',
                                                    bbox={'facecolor': 'black', 'alpha': 0.5, 'pad': 5}, # Add background box
                                                    transform=self.ax_main.transAxes) # Use axes coordinates
        
        # Bottom panel for activity graph (spans bottom row, middle column)
        self.ax_bottom = plt.subplot(gs[1, 1])
        self.ax_bottom.set_title("Module Activity", fontsize=14, color='white')
        self.ax_bottom.set_xlabel("Time (arbitrary units)", fontsize=12, color='white')
        self.ax_bottom.set_ylabel("Activity (fraction active)", fontsize=12, color='white')
        self.ax_bottom.set_ylim(0, 1.05) # Allow slightly above 1 for visual padding
        # x-limits will be set dynamically for sliding window
        self.ax_bottom.tick_params(labelsize=10, colors='white')
        self.ax_bottom.patch.set_facecolor('#333333') # Darker background for graph
        self.ax_bottom.spines['top'].set_color('white')
        self.ax_bottom.spines['bottom'].set_color('white')
        self.ax_bottom.spines['left'].set_color('white')
        self.ax_bottom.spines['right'].set_color('white')
        self.ax_bottom.xaxis.label.set_color('white')
        self.ax_bottom.yaxis.label.set_color('white')
        self.ax_bottom.title.set_color('white')


        # Controls panel (bottom row, left column)
        # Position manually to be precisely in the bottom-left area
        self.ax_controls = self.fig.add_axes([0.05, 0.05, 0.25, 0.2]) # [left, bottom, width, height]
        self.ax_controls.axis('off') # Hide axes for controls
        self.ax_controls.text(0.5, 1.0, "Controls", ha='center', va='top', fontsize=14, color='white', transform=self.ax_controls.transAxes)

        # Input Type Control (Radio Buttons)
        input_type_labels = ['Pattern', 'Random', 'Pulse', 'None']
        # Position manually within the controls area's coordinate system (0 to 1)
        self.ax_input_radio = self.fig.add_axes([0.07, 0.07, 0.1, 0.1]) # [left, bottom, width, height] relative to figure
        self.radio_input = RadioButtons(self.ax_input_radio, input_type_labels, active=0)
        self.radio_input.on_clicked(self.set_input_type)
        # Style radio button labels - Accessible via .labels
        for text in self.radio_input.labels:
             text.set_color('white')
        # Styling radio button circles directly is not reliably supported

        # Speed slider
        self.ax_speed = self.fig.add_axes([0.18, 0.17, 0.12, 0.03]) # [left, bottom, width, height] relative to figure
        self.slider_speed = Slider(self.ax_speed, 'Speed', 0.1, 2.0, valinit=1.0, color='#e74c3c')
        self.slider_speed.label.set_fontsize(10)
        self.slider_speed.label.set_color('white')
        # Styling slider line directly via .yzatu is not supported - Removed the line
        self.slider_speed.on_changed(self.update_speed)

        # Start/Stop button
        self.ax_start_stop = self.fig.add_axes([0.18, 0.12, 0.06, 0.04]) # [left, bottom, width, height] relative to figure
        self.btn_start_stop = Button(self.ax_start_stop, 'Start', color='#2ecc71', hovercolor='#27ae60')
        self.btn_start_stop.label.set_fontsize(10)
        self.btn_start_stop.label.set_color('white')
        self.btn_start_stop.on_clicked(self.toggle_simulation)
        
        # Reset button
        self.ax_reset = self.fig.add_axes([0.25, 0.12, 0.06, 0.04]) # [left, bottom, width, height] relative to figure
        self.btn_reset = Button(self.ax_reset, 'Reset', color='#e74c3c', hovercolor='#c0392b')
        self.btn_reset.label.set_fontsize(10)
        self.btn_reset.label.set_color('white')
        self.btn_reset.on_clicked(self.reset_simulation)

        # Module State Legend panel (bottom row, right column)
        # Position manually to be precisely in the bottom-right area
        self.ax_legend = self.fig.add_axes([0.7, 0.05, 0.25, 0.2]) # [left, bottom, width, height] relative to figure
        self.ax_legend.axis('off') # Hide axes for legend
        self.ax_legend.text(0.5, 1.0, "NPU State Legend", ha='center', va='top', fontsize=14, color='white', transform=self.ax_legend.transAxes)
        self.add_state_legend(self.ax_legend) # Draw legend inside this axes


        # Initialize activity plot lines
        for module_name in self.modules:
            color = self.module_colors[module_name]
            line, = self.ax_bottom.plot([], [], label=module_name.capitalize(), color=color, linewidth=2)
            self.activity_lines[module_name] = line
        self.ax_bottom.legend(fontsize=10, loc='upper left', facecolor='#555555', edgecolor='white', labelcolor='white') # Styled legend


        # Draw static elements of the system (modules, connections) and create initial module outline patches
        self.draw_static_system_elements(self.ax_main)

        # Create initial NPU patches and store references
        # These are static in terms of existence, only their color updates
        for module_name, module in self.modules.items():
             for npu_id, npu in module.npus.items():
                 circle = plt.Circle(npu.position, npu.size, facecolor=npu.get_color(), edgecolor='white', alpha=0.8, zorder=3)
                 self.ax_main.add_patch(circle)
                 self.npu_patches[npu_id] = circle

        # Initialize the list of artists to update for blitting
        # This list will be built dynamically in update_visual_artists
        # Start with persistent artists that always exist but change properties
        self._artists = list(self.npu_patches.values()) + list(self.activity_lines.values()) + list(self.module_outline_patches.values()) + [self.info_text_artist]


        # Initial draw/update to set everything up
        # We don't return artists here, FuncAnimation handles the first draw
        self.update_visual_artists(self.ax_main, self.ax_bottom)

        # FuncAnimation needs the figure object
        return self.fig

    def add_state_legend(self, ax):
        """Add a legend for NPU states within a specific axes."""
        states = [NPUState.RESTING, NPUState.INTEGRATION, NPUState.FIRING, NPUState.REFRACTORY]
        colors_list = ['#1f77b4', '#ff7f0e', '#d62728', '#9467bd'] # Renamed to avoid conflict
        labels = ['Resting', 'Integration', 'Firing', 'Refractory']
        
        # Position legend within the axes using axes coordinates (0 to 1)
        legend_x = 0.1
        legend_y = 0.75
        legend_spacing = 0.15
        
        for i, (state, color, label) in enumerate(zip(states, colors_list, labels)):
            circle = plt.Circle((legend_x, legend_y - i*legend_spacing), 0.05, # Relative size within axes
                                facecolor=color, transform=ax.transAxes)
            ax.add_patch(circle)
            ax.text(legend_x + 0.1, legend_y - i*legend_spacing, label, 
                    ha='left', va='center', fontsize=10, color='white', transform=ax.transAxes)

    def draw_static_system_elements(self, ax):
        """Draw static background elements of the system and create dynamic outline patches."""
        # Draw module connections paths (background)
        for source, target in self.module_connections:
            source_pos = self.modules[source].position
            target_pos = self.modules[target].position
            
            dx = target_pos[0] - source_pos[0]
            dy = target_pos[1] - source_pos[1]
            length = np.sqrt(dx*dx + dy*dy)
            width = 0.5 # Width of the path
            
            # Calculate perpendicular direction
            perp_dx = -dy / length
            perp_dy = dx / length
            
            # Create polygon points for the path
            points = [
                (source_pos[0] + perp_dx * width/2, source_pos[1] + perp_dy * width/2),
                (source_pos[0] - perp_dx * width/2, source_pos[1] - perp_dy * width/2),
                (target_pos[0] - perp_dx * width/2, target_pos[1] - perp_dy * width/2),
                (target_pos[0] + perp_dx * width/2, target_pos[1] + perp_dy * width/2)
            ]
            
            # Draw the path
            path = Polygon(points, closed=True, facecolor='#333333', edgecolor='none', alpha=0.5, zorder=0)
            ax.add_patch(path)
            
            # Add arrow to show direction
            mid_x = (source_pos[0] + target_pos[0]) / 2
            mid_y = (source_pos[1] + target_pos[1]) / 2
            arrow_length = 0.8
            arrow_dx = arrow_length * dx / length
            arrow_dy = arrow_length * dy / length
            
            arrow = FancyArrowPatch((mid_x - arrow_dx/2, mid_y - arrow_dy/2), 
                                   (mid_x + arrow_dx/2, mid_y + arrow_dy/2),
                                   arrowstyle='->', 
                                   mutation_scale=30, # Larger arrow head
                                   linewidth=2,
                                   color='white', 
                                   alpha=0.8,
                                   zorder=1)
            ax.add_patch(arrow)
            
        # Draw modules outlines and create dynamic outline patches
        for module_name, module in self.modules.items():
            color = self.module_colors[module_name]
            # Create module circle outline patch - this will be updated dynamically
            circle = plt.Circle(module.position, module.radius, 
                                facecolor=color, # Use facecolor and alpha for activity
                                edgecolor=color, linestyle='--', linewidth=2, 
                                alpha=0.2, # Start with low alpha
                                zorder=2)
            ax.add_patch(circle)
            self.module_outline_patches[module_name] = circle # Store reference
            
            # Add module label (static)
            ax.text(module.position[0], module.position[1] + module.radius + 0.3, 
                    module_name.capitalize(),
                    ha='center', va='center', fontsize=16, fontweight='bold', color=color, zorder=2)

    def update_visual_artists(self, ax_main, ax_bottom):
        """Update the properties of matplotlib artists based on simulation data."""
        
        # List to hold all artists that were updated or added/removed this frame
        artists_to_update = []

        # --- Update Info Text ---
        info_text = f"Time: {self.current_time:.1f} | Input: {self.input_type.capitalize()}"
        self.info_text_artist.set_text(info_text)
        artists_to_update.append(self.info_text_artist)


        # --- Update NPU colors ---
        # The NPU patches exist permanently, we just update their color if needed
        for module_name, module in self.modules.items():
             for npu_id, npu in module.npus.items():
                 patch = self.npu_patches[npu_id]
                 new_color = npu.get_color()
                 # Check if color actually changed before updating
                 # Use matplotlib.colors.to_rgb for conversion
                 if patch.get_facecolor()[0:3] != colors.to_rgb(new_color): 
                    patch.set_facecolor(new_color)
                 # Add the NPU patch to the list of artists to update regardless, as blit needs it
                 artists_to_update.append(patch)


        # --- Update Module Activity Visualization (Outline Alpha) ---
        for module_name, module in self.modules.items():
             outline_patch = self.module_outline_patches[module_name]
             # Map activity level (0-1) to alpha (e.g., 0.2 to 0.8)
             new_alpha = 0.2 + module.activity_level * 0.6 
             if outline_patch.get_alpha() != new_alpha:
                  outline_patch.set_alpha(new_alpha)
             artists_to_update.append(outline_patch)


        # --- Update Active Spikes ---
        # Remove old spike patches
        for patch in self.spike_patches:
            patch.remove() # Remove from axes
        self.spike_patches = [] # Clear the list

        # Add new spike patches
        for module_name, npu_id in self.active_spikes_data:
            npu = self.modules[module_name].npus[npu_id]
            # Add glow effect (slightly larger, more transparent)
            glow = plt.Circle(npu.position, npu.size * 2.5, facecolor='yellow', edgecolor='none', alpha=0.4, zorder=4)
            ax_main.add_patch(glow)
            self.spike_patches.append(glow)
            artists_to_update.append(glow)

            # Add spike indication (smaller, less transparent)
            spike_circle = plt.Circle(npu.position, npu.size * 1.8, facecolor='yellow', edgecolor='white', alpha=0.9, linewidth=0.5, zorder=5)
            ax_main.add_patch(spike_circle)
            self.spike_patches.append(spike_circle)
            artists_to_update.append(spike_circle)


        # --- Update Flow Particles ---
        # Remove old particle patches (particles that have finished or were removed)
        # We need to match particle data objects to their visual patches
        # Create a mapping from particle data object identity to existing patch tuple for easier update/removal
        particle_data_to_patch = {id(p_data_obj): (p_data_obj, p_patch, g_patch) for p_data_obj, p_patch, g_patch in self.flow_particle_patches}
        
        updated_flow_particle_patches = [] # This will be the new list of active patches

        # Keep track of patches that need to be removed at the end
        patches_to_remove = {patch for data, patch, glow in self.flow_particle_patches}
        glows_to_remove = {glow for data, patch, glow in self.flow_particle_patches}

        for particle_data in self.flow_particles_data:
            particle_id = id(particle_data)
            if particle_id in particle_data_to_patch:
                # Particle already exists, update its patch position
                _, p_patch, g_patch = particle_data_to_patch[particle_id] # Retrieve existing patches
                p_patch.set_center(particle_data['position'])
                g_patch.set_center(particle_data['position'])
                updated_flow_particle_patches.append((particle_data, p_patch, g_patch))
                artists_to_update.append(p_patch)
                artists_to_update.append(g_patch)
                # Mark these patches as *not* needing removal
                patches_to_remove.discard(p_patch)
                glows_to_remove.discard(g_patch)

            else:
                # This is a new particle, create patches
                x, y = particle_data['position']
                size = particle_data['size']
                color = particle_data['color']

                # Add glow effect for particle
                glow = plt.Circle((x, y), size * 1.5, facecolor=color, edgecolor='none', alpha=0.3, zorder=6)
                ax_main.add_patch(glow)
                
                # Add particle circle
                circle = plt.Circle((x, y), size, facecolor=color, edgecolor='white', alpha=1.0, linewidth=0.5, zorder=7)
                ax_main.add_patch(circle)

                updated_flow_particle_patches.append((particle_data, circle, glow))
                artists_to_update.append(circle)
                artists_to_update.append(glow)
                
        # Now, remove the patches that were not updated (meaning their corresponding particle data is gone)
        for patch in patches_to_remove:
             patch.remove()
        for glow in glows_to_remove:
             glow.remove()

        self.flow_particle_patches = updated_flow_particle_patches # Update the list of managed patches


        # --- Update Activity Plot ---
        # We need to track the latest time across all histories to set x-limits
        all_times = []
        for module in self.modules.values():
            if module.activity_history:
                all_times.extend([t for t, _ in module.activity_history])

        max_time = max(all_times, default=0)
        
        # Set x-axis limits for a sliding window showing the last 50 time units
        window_size = 50
        if max_time > window_size:
             ax_bottom.set_xlim(max_time - window_size, max_time)
        else:
             ax_bottom.set_xlim(0, window_size) # Start from 0 if not enough history


        for module_name, line in self.activity_lines.items():
            history = self.modules[module_name].activity_history
            if history:
                times, activities = zip(*history)
                # Set data using absolute time for the x-axis
                line.set_data(times, activities)
            else:
                line.set_data([], []) # No data
            
            # Add the line artist to the update list
            artists_to_update.append(line)


        # Ensure all artists returned are visible and on the correct axes
        # Check if any artists are None or invalid before returning
        # We need to include artists from BOTH ax_main and ax_bottom that were updated
        # This requires collecting artists from both axes in the artists_to_update list.
        # Our current approach adds them all to one list, which is correct for blitting
        valid_artists = [art for art in artists_to_update if art is not None and art.figure is not None]


        return tuple(valid_artists) # Return a tuple for blitting

    def animate(self, frame):
        """Animation function for FuncAnimation."""
        # Update simulation data
        self.update_simulation_data()
        
        # Update visual artists based on new data
        # update_visual_artists will manage adding/removing/updating patches
        # and will return the list of artists that were affected this frame
        return self.update_visual_artists(self.ax_main, self.ax_bottom)
        
    def toggle_simulation(self, event):
        """Toggle simulation running state."""
        self.running = not self.running
        self.btn_start_stop.label.set_text('Stop' if self.running else 'Start')
        self.fig.canvas.draw_idle() # Redraw the button label

    def update_speed(self, val):
        """Update simulation speed."""
        self.speed = val

    def set_input_type(self, label):
        """Set the input pattern type based on radio button selection."""
        # Map label from RadioButtons to the internal key
        input_type_map = {'Pattern': 'pattern', 'Random': 'random', 'Pulse': 'pulse', 'None': 'none'}
        self.input_type = input_type_map.get(label, 'none') # Default to 'none' if not found
        print(f"Input type set to: {self.input_type}")
        # Optional: You might want to trigger a small input burst or reset state when changing input type


    def reset_simulation(self, event):
        """Reset the simulation."""
        self.running = False
        self.btn_start_stop.label.set_text('Start')

        # Reset system state
        self.current_time = 0
        # Activity history is stored within the module objects
        self.active_spikes_data = []
        self.flow_particles_data = []
        
        # Reset modules' internal state
        for module_name, module in self.modules.items():
            module.activity_history = [] # Clear history
            module.activity_level = 0.0 # Reset current level
            for npu_id, npu in module.npus.items():
                npu.membrane_potential = -70.0
                npu.state = NPUState.RESTING
                npu.spike_history = []
                
        # --- Reset Visual Artists ---
        # Remove dynamic patches from axes
        for patch in self.spike_patches:
            patch.remove()
        self.spike_patches = [] # Clear the list

        # Remove flow particle patches from axes
        for particle_data_obj, p_patch, g_patch in self.flow_particle_patches:
             p_patch.remove()
             g_patch.remove()
        self.flow_particle_patches = [] # Clear the list

        # Reset NPU colors to resting state color
        for module_name, module in self.modules.items():
            for npu_id, npu in module.npus.items():
                if npu_id in self.npu_patches:
                     # Get the *current* resting color based on the NPU state after reset
                     self.npu_patches[npu_id].set_facecolor(npu.get_color())

        # Reset module outline alpha
        for module_name, patch in self.module_outline_patches.items():
             patch.set_alpha(0.2) # Reset to low alpha

        # Reset activity plot lines
        for module_name, line in self.activity_lines.items():
            line.set_data([], []) # Clear data
        self.ax_bottom.set_xlim(0, 50) # Reset x-limit view for the fixed window


        # Reset info text
        self.info_text_artist.set_text("")

        # Force a full redraw after resetting artists
        # FuncAnimation might be paused, so draw_idle is necessary
        self.fig.canvas.draw_idle()


    def run(self):
        """Run the interactive demo."""
        # Set up visualization
        fig = self.setup_visualization()
        
        # Create animation
        # blit=True helps performance by only redrawing the artists that change
        # We need to return *all* artists that change in animate()
        # Using interval=30 (30ms) means roughly 33 frames per second
        self.ani = FuncAnimation(fig, self.animate, frames=None, interval=30, blit=True) 

        print("Starting NeuronOS Enhanced Demo...")
        print("This demo shows how the NeuronOS architecture processes information through specialized neural modules.")
        print("\nWhat you're seeing:")
        print("- Three neural modules: Sensory (blue), Processing (green), Executive (red)")
        print("- Colored circles represent Neural Processing Units (NPUs) in different states (see legend)")
        print("- Moving colored particles show information flowing between modules along the grey paths")
        print("- Yellow glows highlight NPUs that have just fired (spiked)")
        print("- Module outlines become brighter as their activity level increases")
        print("- The graph shows activity levels (fraction of active NPUs) of each module over time, with a sliding window")
        print("- Dynamic text shows current simulation time and input type")
        print("\nControls:")
        print("- Start/Stop: Begin or pause the simulation")
        print("- Speed: Adjust how fast the simulation runs")
        print("- Reset: Return to the initial state")
        print("- Input Type: Change the pattern of input signals to the Sensory module")
        print("\nIMPORTANT: Click the 'Start' button to begin the simulation!")

        # Show plot
        # plt.tight_layout() # Might interfere with custom positioning - Keep commented
        plt.show()

# Run the demo if executed directly
if __name__ == "__main__":
    demo = NeuronOSEnhancedDemo()
    demo.run()
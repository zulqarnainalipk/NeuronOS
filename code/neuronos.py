import numpy as np
import time
from enum import Enum
from collections import defaultdict

# Import NeuronOS components
from npu import NeuralProcessingUnit, NPUState
from cpm import CorticalProcessingModule, CPMType
from neural_highway import NeuralHighway
from neuromodulatory_system import NeuromodulatorySystem, ModulationType

class NeuronOS:
    """
    Main implementation of the NeuronOS architecture that integrates all components
    into a complete neuromorphic computing system.
    """
    
    def __init__(self, config=None):
        """
        Initialize the NeuronOS system with the specified configuration.
        
        Args:
            config: Optional configuration dictionary with system parameters
        """
        # Use default configuration if none provided
        self.config = config or self._get_default_config()
        
        # Initialize system time
        self.current_time = 0.0
        self.time_step = self.config.get('time_step', 1.0)  # ms
        
        # Initialize components
        self._initialize_components()
        
        # System state
        self.running = False
        self.execution_history = []
        
    def _get_default_config(self):
        """Get default configuration for NeuronOS."""
        return {
            'time_step': 1.0,  # ms
            'simulation_duration': 1000.0,  # ms
            'cpm_config': {
                'sensory': {'count': 1, 'input_size': 100, 'hidden_size': 500, 'output_size': 50},
                'temporal': {'count': 1, 'input_size': 50, 'hidden_size': 200, 'output_size': 30},
                'spatial': {'count': 1, 'input_size': 50, 'hidden_size': 200, 'output_size': 30},
                'linguistic': {'count': 1, 'input_size': 50, 'hidden_size': 200, 'output_size': 30},
                'executive': {'count': 1, 'input_size': 90, 'hidden_size': 300, 'output_size': 50},
                'memory': {'count': 1, 'input_size': 50, 'hidden_size': 500, 'output_size': 50}
            },
            'highway_config': {
                'bandwidth': 1000
            }
        }
        
    def _initialize_components(self):
        """Initialize all NeuronOS components based on configuration."""
        # Initialize Cortical Processing Modules
        self.cpms = {}
        
        # Create CPMs based on configuration
        for cpm_type_name, config in self.config['cpm_config'].items():
            cpm_type = CPMType[cpm_type_name.upper()]
            for i in range(config['count']):
                cpm_id = f"{cpm_type_name}_{i}"
                self.cpms[cpm_id] = CorticalProcessingModule(
                    cpm_id, 
                    cpm_type,
                    config['input_size'],
                    config['hidden_size'],
                    config['output_size']
                )
        
        # Initialize Neural Highways
        self.highways = {}
        
        # Create main highway
        main_highway_id = "main_highway"
        self.highways[main_highway_id] = NeuralHighway(
            main_highway_id,
            self.config['highway_config']['bandwidth']
        )
        
        # Connect CPMs to the main highway
        for source_id in self.cpms:
            for target_id in self.cpms:
                if source_id != target_id:
                    # Different connection priorities based on CPM types
                    priority = 1.0
                    
                    # Higher priority for executive module connections
                    if "executive" in source_id or "executive" in target_id:
                        priority = 1.5
                        
                    # Higher priority for sensory to processing connections
                    if "sensory" in source_id and any(t in target_id for t in ["temporal", "spatial", "linguistic"]):
                        priority = 1.3
                        
                    self.highways[main_highway_id].add_connection(source_id, target_id, priority)
        
        # Initialize Neuromodulatory System
        self.neuromodulatory_system = NeuromodulatorySystem()
        
        # Input and output buffers
        self.input_buffer = {}  # Maps input_id to list of input values
        self.output_buffer = {}  # Maps output_id to list of output values
        
    def process_input(self, input_data):
        """
        Process external input data through the system.
        
        Args:
            input_data: Dictionary mapping input_id to input values
            
        Returns:
            Dictionary of output values
        """
        # Store input in buffer
        self.input_buffer = input_data
        
        # Convert input data to spikes for sensory CPMs
        sensory_spikes = {}
        for input_id, values in input_data.items():
            # Determine which sensory module should receive this input
            target_cpm = None
            for cpm_id in self.cpms:
                if "sensory" in cpm_id:
                    target_cpm = cpm_id
                    break
                    
            if target_cpm:
                # Convert values to spike indices and times
                spikes = []
                for i, value in enumerate(values):
                    if value > 0.5:  # Simple threshold for spike generation
                        spikes.append((i, self.current_time))
                        
                sensory_spikes[target_cpm] = spikes
        
        # Process sensory input
        cpm_outputs = {}
        for cpm_id, spikes in sensory_spikes.items():
            output = self.cpms[cpm_id].process_input(spikes, self.current_time, self.time_step)
            cpm_outputs[cpm_id] = output
            
        # Transmit spikes through Neural Highways
        for source_id, spikes in cpm_outputs.items():
            for output_index, spike_time in spikes:
                # Find all potential targets
                for target_id in self.cpms:
                    if target_id != source_id:
                        # Transmit spike with default urgency and importance
                        self.highways["main_highway"].transmit_spike(
                            source_id, target_id, output_index, spike_time, 1.0, 1.0
                        )
        
        # Process highway transmissions
        delivered_spikes = {}
        for highway_id, highway in self.highways.items():
            delivered = highway.update(self.current_time, self.time_step)
            delivered_spikes[highway_id] = delivered
            
        # Deliver spikes to target CPMs
        for highway_id, spikes in delivered_spikes.items():
            for target_id, source_id, spike_data in spikes:
                if target_id in self.cpms:
                    # Convert to input format expected by CPM
                    cpm_input = [(int(spike_data), self.current_time)]
                    output = self.cpms[target_id].process_input(cpm_input, self.current_time, self.time_step)
                    
                    # Store or update output
                    if target_id in cpm_outputs:
                        cpm_outputs[target_id].extend(output)
                    else:
                        cpm_outputs[target_id] = output
        
        # Get activity levels for neuromodulation
        module_activities = {}
        for cpm_id, cpm in self.cpms.items():
            module_activities[cpm_id] = cpm.get_activity_level()
            
        # Update neuromodulatory system
        modulation_factors = self.neuromodulatory_system.update(
            self.current_time, self.time_step, module_activities
        )
        
        # Apply neuromodulation to CPMs
        for cpm_id, factors in modulation_factors.items():
            if cpm_id in self.cpms:
                # Calculate overall modulation factor (simplified)
                attention = factors[ModulationType.ATTENTION]
                reward = factors[ModulationType.REWARD]
                homeostatic = factors[ModulationType.HOMEOSTATIC]
                plasticity = factors[ModulationType.PLASTICITY]
                
                # Apply modulation (simplified - in a full implementation this would be more complex)
                overall_modulation = attention * reward * homeostatic
                self.cpms[cpm_id].set_modulation(overall_modulation)
        
        # Collect outputs from executive module
        outputs = {}
        for cpm_id, output_spikes in cpm_outputs.items():
            if "executive" in cpm_id:
                # Convert spikes to output values
                for output_index, spike_time in output_spikes:
                    if output_index not in outputs:
                        outputs[output_index] = 0
                    outputs[output_index] += 1  # Count spikes
                    
        # Normalize outputs
        max_count = max(outputs.values()) if outputs else 1
        normalized_outputs = {k: v / max_count for k, v in outputs.items()}
        
        # Store in output buffer
        self.output_buffer = normalized_outputs
        
        # Update system time
        self.current_time += self.time_step
        
        # Record execution history
        self.execution_history.append({
            'time': self.current_time,
            'inputs': input_data,
            'outputs': normalized_outputs,
            'activity': module_activities
        })
        
        return normalized_outputs
        
    def run_simulation(self, input_sequence, duration=None):
        """
        Run a simulation with the provided input sequence.
        
        Args:
            input_sequence: List of input data dictionaries for each time step
            duration: Optional duration to run (defaults to config value)
            
        Returns:
            List of output dictionaries for each time step
        """
        self.running = True
        self.current_time = 0.0
        
        # Use configured duration if none provided
        if duration is None:
            duration = self.config.get('simulation_duration', 1000.0)
            
        # Reset execution history
        self.execution_history = []
        
        # Run simulation
        outputs = []
        time_steps = int(duration / self.time_step)
        
        for t in range(time_steps):
            # Get input for this time step (if available)
            input_data = input_sequence[t] if t < len(input_sequence) else {}
            
            # Process input
            output = self.process_input(input_data)
            outputs.append(output)
            
            # Check if simulation should continue
            if not self.running:
                break
                
        return outputs
        
    def stop_simulation(self):
        """Stop the current simulation."""
        self.running = False
        
    def reset(self):
        """Reset the system to initial state."""
        self.current_time = 0.0
        self._initialize_components()
        self.execution_history = []
        
    def get_system_state(self):
        """Get the current state of the system."""
        return {
            'time': self.current_time,
            'cpms': {cpm_id: {'activity': cpm.get_activity_level()} for cpm_id, cpm in self.cpms.items()},
            'highways': {hw_id: {'congestion': hw.get_congestion_level()} for hw_id, hw in self.highways.items()},
            'neuromodulation': {
                'attention': self.neuromodulatory_system.attention_level,
                'reward': self.neuromodulatory_system.reward_signal,
                'plasticity': self.neuromodulatory_system.plasticity_rate
            }
        }
        
    def provide_reward(self, reward_value):
        """Provide a reward signal to the system."""
        self.neuromodulatory_system.provide_reward(reward_value)
        
    def focus_attention(self, focus_areas):
        """Focus attention on specific modules or inputs."""
        self.neuromodulatory_system.set_attention_focus(focus_areas)


# Example usage
if __name__ == "__main__":
    # Create NeuronOS instance
    neuronos = NeuronOS()
    
    # Create a simple input sequence (random data for demonstration)
    input_sequence = []
    for t in range(100):
        # Random binary input pattern
        input_values = np.random.rand(100) > 0.9
        input_data = {'visual_input': input_values.astype(float)}
        input_sequence.append(input_data)
    
    # Run simulation
    print("Running NeuronOS simulation...")
    outputs = neuronos.run_simulation(input_sequence, duration=100.0)
    
    # Print summary
    print(f"Simulation completed with {len(outputs)} time steps")
    print(f"Final system state: {neuronos.get_system_state()}")
    
    # Example of providing reward and focusing attention
    neuronos.provide_reward(0.8)  # Positive reward
    neuronos.focus_attention({'executive_0': 0.9, 'memory_0': 0.7})  # Focus on executive and memory modules
    
    print("System state after modulation:", neuronos.get_system_state())

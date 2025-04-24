from enum import Enum
import numpy as np
from collections import defaultdict
import heapq

class CPMType(Enum):
    SENSORY = 0
    TEMPORAL = 1
    SPATIAL = 2
    LINGUISTIC = 3
    EXECUTIVE = 4
    MEMORY = 5

class CorticalProcessingModule:
    """
    Implementation of a Cortical Processing Module (CPM) that organizes NPUs into a
    specialized functional unit for specific types of information processing.
    """
    
    def __init__(self, id, cpm_type, input_size, hidden_size, output_size):
        """
        Initialize a Cortical Processing Module with configurable parameters.
        
        Args:
            id: Unique identifier for the CPM
            cpm_type: Type of CPM (sensory, temporal, spatial, etc.)
            input_size: Number of input NPUs
            hidden_size: Number of hidden layer NPUs
            output_size: Number of output NPUs
        """
        self.id = id
        self.cpm_type = cpm_type
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        # Initialize NPUs for each layer
        from npu import NeuralProcessingUnit
        
        # Input layer NPUs
        self.input_npus = {}
        for i in range(input_size):
            npu_id = f"{id}_input_{i}"
            self.input_npus[npu_id] = NeuralProcessingUnit(npu_id)
        
        # Hidden layer NPUs
        self.hidden_npus = {}
        for i in range(hidden_size):
            npu_id = f"{id}_hidden_{i}"
            self.hidden_npus[npu_id] = NeuralProcessingUnit(npu_id)
        
        # Output layer NPUs
        self.output_npus = {}
        for i in range(output_size):
            npu_id = f"{id}_output_{i}"
            self.output_npus[npu_id] = NeuralProcessingUnit(npu_id)
        
        # Connect layers with initial random weights
        self._connect_layers()
        
        # Module state
        self.active = True
        self.local_modulation = 1.0  # Modulation factor for local activity
        
        # Activity tracking
        self.activity_history = []
        self.output_history = []
        
        # Configuration parameters based on CPM type
        self._configure_for_type()
    
    def _connect_layers(self):
        """Connect NPUs between layers with initial random weights."""
        # Connect input to hidden layer
        for input_id, input_npu in self.input_npus.items():
            for hidden_id, hidden_npu in self.hidden_npus.items():
                weight = np.random.uniform(0.1, 0.5)
                input_npu.add_synapse(hidden_id, weight)
        
        # Connect hidden to output layer
        for hidden_id, hidden_npu in self.hidden_npus.items():
            for output_id, output_npu in self.output_npus.items():
                weight = np.random.uniform(0.1, 0.5)
                hidden_npu.add_synapse(output_id, weight)
    
    def _configure_for_type(self):
        """Configure module parameters based on CPM type."""
        if self.cpm_type == CPMType.SENSORY:
            # Sensory modules have faster response times
            for npu in list(self.input_npus.values()) + list(self.hidden_npus.values()) + list(self.output_npus.values()):
                npu.membrane_time_constant = 5.0
                npu.refractory_period = 1.0
        
        elif self.cpm_type == CPMType.TEMPORAL:
            # Temporal modules have recurrent connections
            for i, hidden_id in enumerate(self.hidden_npus):
                for j, target_id in enumerate(self.hidden_npus):
                    if i != j:  # No self-connections
                        weight = np.random.uniform(0.05, 0.2)
                        self.hidden_npus[hidden_id].add_synapse(target_id, weight)
        
        elif self.cpm_type == CPMType.MEMORY:
            # Memory modules have stronger recurrent connections
            for i, hidden_id in enumerate(self.hidden_npus):
                for j, target_id in enumerate(self.hidden_npus):
                    if i != j:  # No self-connections
                        weight = np.random.uniform(0.3, 0.6)
                        self.hidden_npus[hidden_id].add_synapse(target_id, weight)
    
    def process_input(self, input_spikes, current_time, time_step):
        """
        Process input spikes through the CPM.
        
        Args:
            input_spikes: List of (input_index, spike_time) tuples
            current_time: Current simulation time (ms)
            time_step: Duration of time step (ms)
            
        Returns:
            List of (output_index, spike_time) tuples
        """
        if not self.active:
            return []
        
        # Deliver input spikes to input layer NPUs
        for input_index, spike_time in input_spikes:
            if 0 <= input_index < self.input_size:
                input_id = f"{self.id}_input_{input_index}"
                # Create a dummy source ID for external inputs
                self.input_npus[input_id].receive_spike("external", spike_time)
        
        # Process input layer
        hidden_spikes = []
        for input_id, input_npu in self.input_npus.items():
            spikes = input_npu.update(current_time, time_step)
            hidden_spikes.extend(spikes)
        
        # Process hidden layer
        output_spikes = []
        for hidden_id, hidden_npu in self.hidden_npus.items():
            # Receive spikes from input layer
            for target_id, spike_time in hidden_spikes:
                if target_id == hidden_id:
                    hidden_npu.receive_spike(target_id.split('_')[0], spike_time)
            
            # Update hidden NPU
            spikes = hidden_npu.update(current_time, time_step)
            output_spikes.extend(spikes)
        
        # Process output layer
        final_output = []
        for output_id, output_npu in self.output_npus.items():
            # Receive spikes from hidden layer
            for target_id, spike_time in output_spikes:
                if target_id == output_id:
                    output_npu.receive_spike(target_id.split('_')[0], spike_time)
            
            # Update output NPU
            spikes = output_npu.update(current_time, time_step)
            
            # Convert internal output spikes to output indices
            for _, spike_time in spikes:
                output_index = int(output_id.split('_')[-1])
                final_output.append((output_index, spike_time))
        
        # Track activity
        total_activity = sum(1 for npu in list(self.input_npus.values()) + 
                             list(self.hidden_npus.values()) + 
                             list(self.output_npus.values()) 
                             if npu.state.value > 0)
        self.activity_history.append((current_time, total_activity))
        
        # Track output
        self.output_history.append((current_time, final_output))
        
        return final_output
    
    def set_modulation(self, modulation_factor):
        """Set the local modulation factor for this CPM."""
        self.local_modulation = max(0.1, min(2.0, modulation_factor))
        
        # Apply modulation to NPU thresholds
        for npu in list(self.input_npus.values()) + list(self.hidden_npus.values()) + list(self.output_npus.values()):
            # Higher modulation lowers threshold (makes firing easier)
            base_threshold = -55.0
            npu.threshold = base_threshold / self.local_modulation
    
    def get_activity_level(self):
        """Get the current activity level of the CPM."""
        if not self.activity_history:
            return 0.0
        
        # Return average activity over recent history
        recent_activity = [activity for _, activity in self.activity_history[-10:]]
        return sum(recent_activity) / len(recent_activity) if recent_activity else 0.0

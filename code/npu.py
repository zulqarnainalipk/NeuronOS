# Neural Processing Unit (NPU) Implementation

import numpy as np
from enum import Enum

class NPUState(Enum):
    RESTING = 0
    INTEGRATION = 1
    FIRING = 2
    REFRACTORY = 3

class NeuralProcessingUnit:
    """
    Implementation of a Neural Processing Unit (NPU) that mimics both neural and synaptic behaviors
    based on the single-transistor artificial neuron technology.
    """
    
    def __init__(self, id, resting_potential=-70.0, threshold=-55.0, reset_potential=-75.0, 
                 membrane_time_constant=10.0, refractory_period=2.0):
        """
        Initialize a Neural Processing Unit with configurable parameters.
        
        Args:
            id: Unique identifier for the NPU
            resting_potential: Baseline membrane potential (mV)
            threshold: Firing threshold potential (mV)
            reset_potential: Potential after firing (mV)
            membrane_time_constant: Time constant for potential decay (ms)
            refractory_period: Duration of refractory period after firing (ms)
        """
        self.id = id
        self.resting_potential = resting_potential
        self.threshold = threshold
        self.reset_potential = reset_potential
        self.membrane_time_constant = membrane_time_constant
        self.refractory_period = refractory_period
        
        # Current state
        self.membrane_potential = resting_potential
        self.state = NPUState.RESTING
        self.refractory_time_remaining = 0.0
        
        # Synaptic connections
        self.synapses = {}  # Maps target NPU IDs to synaptic weights
        self.input_buffer = []  # Incoming spikes with timestamps
        
        # Learning parameters
        self.stdp_window = 20.0  # Time window for STDP (ms)
        self.stdp_a_plus = 0.1   # STDP potentiation strength
        self.stdp_a_minus = 0.12  # STDP depression strength
        self.stdp_tau_plus = 10.0  # STDP potentiation time constant
        self.stdp_tau_minus = 10.0  # STDP depression time constant
        
        # Activity tracking
        self.last_spike_time = 0.0
        self.spike_history = []
        
    def add_synapse(self, target_id, weight=0.5):
        """Add or update a synaptic connection to another NPU."""
        self.synapses[target_id] = weight
        
    def receive_spike(self, source_id, timestamp):
        """Receive a spike from another NPU."""
        self.input_buffer.append((source_id, timestamp))
        
    def update(self, current_time, time_step):
        """
        Update the NPU state for the current time step.
        
        Args:
            current_time: Current simulation time (ms)
            time_step: Duration of time step (ms)
            
        Returns:
            List of (target_id, spike_time) tuples if the NPU fires, empty list otherwise
        """
        output_spikes = []
        
        # Handle refractory period
        if self.state == NPUState.REFRACTORY:
            self.refractory_time_remaining -= time_step
            if self.refractory_time_remaining <= 0:
                self.state = NPUState.RESTING
                self.refractory_time_remaining = 0
                
        # Process incoming spikes
        input_current = 0.0
        for source_id, spike_time in self.input_buffer:
            if current_time - spike_time <= time_step:  # Only process recent spikes
                # Apply synaptic weight (assuming source_id is directly connected)
                input_current += 1.0  # Normalized input
                
                # Apply STDP if this NPU has fired recently
                if self.spike_history and source_id in self.synapses:
                    for spike_time in self.spike_history:
                        delta_t = spike_time - current_time
                        if abs(delta_t) < self.stdp_window:
                            self._apply_stdp(source_id, delta_t)
        
        # Clear processed spikes
        self.input_buffer = [(s, t) for s, t in self.input_buffer 
                             if current_time - t > time_step]
        
        # Update membrane potential based on current state
        if self.state != NPUState.REFRACTORY:
            # Leaky integration
            self.membrane_potential += (
                (self.resting_potential - self.membrane_potential) / self.membrane_time_constant * time_step
                + input_current
            )
            
            # Check for threshold crossing
            if self.membrane_potential >= self.threshold:
                # Generate spike
                self.state = NPUState.FIRING
                self.last_spike_time = current_time
                self.spike_history.append(current_time)
                if len(self.spike_history) > 10:  # Keep history limited
                    self.spike_history.pop(0)
                
                # Reset membrane potential and enter refractory period
                self.membrane_potential = self.reset_potential
                self.refractory_time_remaining = self.refractory_period
                self.state = NPUState.REFRACTORY
                
                # Generate output spikes to all connected NPUs
                for target_id in self.synapses:
                    output_spikes.append((target_id, current_time))
            elif input_current > 0:
                self.state = NPUState.INTEGRATION
            else:
                self.state = NPUState.RESTING
                
        return output_spikes
    
    def _apply_stdp(self, source_id, delta_t):
        """
        Apply Spike-Timing-Dependent Plasticity to update synaptic weight.
        
        Args:
            source_id: ID of the source NPU
            delta_t: Time difference between post and pre-synaptic spikes (ms)
        """
        if source_id not in self.synapses:
            return
            
        weight = self.synapses[source_id]
        
        if delta_t > 0:  # Post-synaptic spike after pre-synaptic spike (potentiation)
            dw = self.stdp_a_plus * np.exp(-delta_t / self.stdp_tau_plus)
            weight += dw
        else:  # Pre-synaptic spike after post-synaptic spike (depression)
            dw = self.stdp_a_minus * np.exp(delta_t / self.stdp_tau_minus)
            weight -= dw
            
        # Ensure weight stays in valid range
        weight = max(0.0, min(1.0, weight))
        self.synapses[source_id] = weight

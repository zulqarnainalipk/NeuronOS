import numpy as np
from enum import Enum
from collections import defaultdict

class ModulationType(Enum):
    ATTENTION = 0
    REWARD = 1
    HOMEOSTATIC = 2
    PLASTICITY = 3

class NeuromodulatorySystem:
    """
    Implementation of the Neuromodulatory System that regulates global system states
    and learning processes in the NeuronOS architecture, inspired by neurotransmitters
    in the human brain.
    """
    
    def __init__(self):
        """Initialize the Neuromodulatory System with default parameters."""
        # Modulation parameters
        self.attention_level = 0.5  # Global attention level (0.0-1.0)
        self.reward_signal = 0.0    # Current reward signal (-1.0 to 1.0)
        self.homeostatic_target = 0.2  # Target activity level (0.0-1.0)
        self.plasticity_rate = 0.5  # Global learning rate (0.0-1.0)
        
        # Module-specific modulation
        self.module_attention = defaultdict(lambda: 0.5)  # Maps module_id to attention level
        self.module_reward = defaultdict(lambda: 0.0)     # Maps module_id to reward signal
        self.module_homeostasis = defaultdict(lambda: 0.2)  # Maps module_id to homeostatic target
        self.module_plasticity = defaultdict(lambda: 0.5)   # Maps module_id to plasticity rate
        
        # Activity tracking
        self.module_activity = defaultdict(lambda: 0.0)   # Maps module_id to current activity level
        self.system_activity = 0.0  # Overall system activity level
        
        # History tracking
        self.attention_history = []
        self.reward_history = []
        self.homeostatic_history = []
        self.plasticity_history = []
        
        # Temporal dynamics
        self.attention_decay = 0.95  # Attention decay factor per time step
        self.reward_decay = 0.9      # Reward decay factor per time step
        
    def update(self, current_time, time_step, module_activities):
        """
        Update the neuromodulatory state based on current system activity.
        
        Args:
            current_time: Current simulation time (ms)
            time_step: Duration of time step (ms)
            module_activities: Dictionary mapping module_id to activity level (0.0-1.0)
            
        Returns:
            Dictionary mapping module_id to dictionary of modulation factors
        """
        # Update activity tracking
        for module_id, activity in module_activities.items():
            self.module_activity[module_id] = activity
            
        # Calculate system-wide activity
        if module_activities:
            self.system_activity = sum(module_activities.values()) / len(module_activities)
        
        # Apply temporal dynamics
        self.attention_level *= self.attention_decay
        self.reward_signal *= self.reward_decay
        
        # Apply homeostatic regulation
        self._apply_homeostatic_regulation()
        
        # Update history
        self.attention_history.append((current_time, self.attention_level))
        self.reward_history.append((current_time, self.reward_signal))
        self.homeostatic_history.append((current_time, self.homeostatic_target))
        self.plasticity_history.append((current_time, self.plasticity_rate))
        
        # Generate modulation factors for each module
        modulation_factors = {}
        for module_id in module_activities.keys():
            modulation_factors[module_id] = {
                ModulationType.ATTENTION: self._get_attention_modulation(module_id),
                ModulationType.REWARD: self._get_reward_modulation(module_id),
                ModulationType.HOMEOSTATIC: self._get_homeostatic_modulation(module_id),
                ModulationType.PLASTICITY: self._get_plasticity_modulation(module_id)
            }
            
        return modulation_factors
        
    def set_attention_focus(self, focus_areas):
        """
        Set the focus of attention to specific modules or inputs.
        
        Args:
            focus_areas: Dictionary mapping module_id to attention level (0.0-1.0)
        """
        # Reset all module attention to base level
        for module_id in self.module_attention:
            self.module_attention[module_id] = 0.2  # Low base attention
            
        # Apply focused attention
        for module_id, attention in focus_areas.items():
            self.module_attention[module_id] = min(1.0, max(0.0, attention))
            
        # Update global attention level
        if focus_areas:
            self.attention_level = sum(focus_areas.values()) / len(focus_areas)
        
    def provide_reward(self, reward_value, target_modules=None):
        """
        Provide a reward signal to the system or specific modules.
        
        Args:
            reward_value: Reward signal value (-1.0 to 1.0)
            target_modules: Optional list of module_ids to receive the reward
        """
        # Update global reward signal
        self.reward_signal = min(1.0, max(-1.0, reward_value))
        
        if target_modules:
            # Apply reward to specific modules
            for module_id in target_modules:
                self.module_reward[module_id] = self.reward_signal
        else:
            # Apply reward system-wide
            for module_id in self.module_reward:
                self.module_reward[module_id] = self.reward_signal
                
    def adjust_plasticity(self, plasticity_rate, target_modules=None):
        """
        Adjust the plasticity rate for the system or specific modules.
        
        Args:
            plasticity_rate: New plasticity rate (0.0-1.0)
            target_modules: Optional list of module_ids to adjust
        """
        # Update global plasticity rate
        self.plasticity_rate = min(1.0, max(0.0, plasticity_rate))
        
        if target_modules:
            # Apply to specific modules
            for module_id in target_modules:
                self.module_plasticity[module_id] = self.plasticity_rate
        else:
            # Apply system-wide
            for module_id in self.module_plasticity:
                self.module_plasticity[module_id] = self.plasticity_rate
                
    def set_homeostatic_target(self, target_activity, target_modules=None):
        """
        Set the homeostatic target activity level for the system or specific modules.
        
        Args:
            target_activity: Target activity level (0.0-1.0)
            target_modules: Optional list of module_ids to adjust
        """
        # Update global homeostatic target
        self.homeostatic_target = min(1.0, max(0.0, target_activity))
        
        if target_modules:
            # Apply to specific modules
            for module_id in target_modules:
                self.module_homeostasis[module_id] = self.homeostatic_target
        else:
            # Apply system-wide
            for module_id in self.module_homeostasis:
                self.module_homeostasis[module_id] = self.homeostatic_target
    
    def _apply_homeostatic_regulation(self):
        """Apply homeostatic regulation based on current activity levels."""
        for module_id, activity in self.module_activity.items():
            target = self.module_homeostasis[module_id]
            
            # Calculate activity error
            error = activity - target
            
            # Adjust module-specific plasticity based on error
            if abs(error) > 0.1:  # Only adjust if error is significant
                # Increase plasticity when activity is too low
                if error < 0:
                    self.module_plasticity[module_id] = min(1.0, self.module_plasticity[module_id] * 1.1)
                # Decrease plasticity when activity is too high
                else:
                    self.module_plasticity[module_id] = max(0.1, self.module_plasticity[module_id] * 0.9)
    
    def _get_attention_modulation(self, module_id):
        """Get the attention modulation factor for a specific module."""
        # Combine global and module-specific attention
        return 0.3 * self.attention_level + 0.7 * self.module_attention[module_id]
    
    def _get_reward_modulation(self, module_id):
        """Get the reward modulation factor for a specific module."""
        # Combine global and module-specific reward
        base_reward = 0.3 * self.reward_signal + 0.7 * self.module_reward[module_id]
        
        # Convert from -1,1 range to 0,2 range (1.0 is neutral)
        return base_reward + 1.0
    
    def _get_homeostatic_modulation(self, module_id):
        """Get the homeostatic modulation factor for a specific module."""
        activity = self.module_activity[module_id]
        target = self.module_homeostasis[module_id]
        
        # Calculate modulation factor based on activity error
        error = activity - target
        
        # Generate modulation factor (1.0 is neutral)
        if error < 0:
            # Activity too low - increase excitability
            return 1.0 + min(0.5, abs(error))
        else:
            # Activity too high - decrease excitability
            return 1.0 - min(0.5, error)
    
    def _get_plasticity_modulation(self, module_id):
        """Get the plasticity modulation factor for a specific module."""
        # Combine global and module-specific plasticity
        return 0.3 * self.plasticity_rate + 0.7 * self.module_plasticity[module_id]

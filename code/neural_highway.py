import numpy as np
import heapq
from collections import defaultdict

class NeuralHighway:
    """
    Implementation of Neural Highways that facilitate spike-based communication
    between Cortical Processing Modules (CPMs) in the NeuronOS architecture.
    """
    
    def __init__(self, id, bandwidth=1000):
        """
        Initialize a Neural Highway with configurable parameters.
        
        Args:
            id: Unique identifier for the Neural Highway
            bandwidth: Maximum number of spikes that can be transmitted per time step
        """
        self.id = id
        self.bandwidth = bandwidth
        
        # Connection topology
        self.connections = defaultdict(list)  # Maps source_id to list of (target_id, priority) tuples
        
        # Transmission queue (priority queue for spike routing)
        self.transmission_queue = []  # Heap of (priority, timestamp, source_id, target_id, spike_data) tuples
        
        # Traffic statistics
        self.traffic_history = []
        self.congestion_points = defaultdict(int)
        
        # Adaptive routing parameters
        self.route_strength = defaultdict(lambda: defaultdict(float))  # Maps (source, target) to strength
        self.learning_rate = 0.01
        
    def add_connection(self, source_id, target_id, priority=1.0):
        """
        Add a connection between two modules.
        
        Args:
            source_id: ID of the source module
            target_id: ID of the target module
            priority: Base priority for this connection (higher values = higher priority)
        """
        self.connections[source_id].append((target_id, priority))
        
    def transmit_spike(self, source_id, target_id, spike_data, timestamp, urgency=1.0, importance=1.0):
        """
        Queue a spike for transmission from source to target.
        
        Args:
            source_id: ID of the source module
            target_id: ID of the target module
            spike_data: Data payload of the spike
            timestamp: Current simulation time
            urgency: Time sensitivity factor (higher = more urgent)
            importance: Relevance factor (higher = more important)
            
        Returns:
            True if spike was queued, False if connection doesn't exist
        """
        # Check if connection exists
        if not any(t[0] == target_id for t in self.connections[source_id]):
            return False
            
        # Calculate priority based on base priority, urgency, and importance
        base_priority = next(p for t, p in self.connections[source_id] if t == target_id)
        priority = base_priority * urgency * importance
        
        # Add to transmission queue (negative priority because heapq is a min-heap)
        heapq.heappush(self.transmission_queue, (-priority, timestamp, source_id, target_id, spike_data))
        return True
        
    def update(self, current_time, time_step):
        """
        Process the transmission queue for the current time step.
        
        Args:
            current_time: Current simulation time
            time_step: Duration of time step
            
        Returns:
            List of (target_id, source_id, spike_data) tuples for delivered spikes
        """
        # Calculate available bandwidth for this time step
        available_bandwidth = self.bandwidth
        
        # Track traffic for this time step
        queue_size = len(self.transmission_queue)
        self.traffic_history.append((current_time, queue_size))
        
        # Process queue up to bandwidth limit
        delivered_spikes = []
        congestion = defaultdict(int)
        
        while self.transmission_queue and available_bandwidth > 0:
            # Pop highest priority spike
            neg_priority, timestamp, source_id, target_id, spike_data = heapq.heappop(self.transmission_queue)
            priority = -neg_priority
            
            # Check if spike is still relevant (not too old)
            if current_time - timestamp > 50.0:  # Discard spikes older than 50ms
                continue
                
            # Deliver the spike
            delivered_spikes.append((target_id, source_id, spike_data))
            available_bandwidth -= 1
            
            # Strengthen this route based on successful transmission
            self.route_strength[source_id][target_id] += self.learning_rate
            
        # If we still have spikes in the queue, record congestion
        if self.transmission_queue:
            for _, _, source_id, target_id, _ in self.transmission_queue:
                congestion_key = f"{source_id}->{target_id}"
                congestion[congestion_key] += 1
                self.congestion_points[congestion_key] += 1
                
        return delivered_spikes
        
    def get_optimal_route(self, source_id, target_id):
        """
        Get the optimal route from source to target based on learned strengths.
        
        Args:
            source_id: ID of the source module
            target_id: ID of the target module
            
        Returns:
            List of module IDs representing the optimal route, or None if no route exists
        """
        # This is a simplified implementation - in a full system, this would use
        # a more sophisticated routing algorithm like Dijkstra's
        
        # Check direct connection
        if any(t[0] == target_id for t in self.connections[source_id]):
            return [source_id, target_id]
            
        # Simple breadth-first search for a route
        visited = set([source_id])
        queue = [(source_id, [source_id])]
        
        while queue:
            current, path = queue.pop(0)
            
            for next_id, _ in self.connections[current]:
                if next_id == target_id:
                    return path + [next_id]
                    
                if next_id not in visited:
                    visited.add(next_id)
                    queue.append((next_id, path + [next_id]))
                    
        return None  # No route found
        
    def get_congestion_level(self):
        """Get the current congestion level of the Neural Highway."""
        if not self.traffic_history:
            return 0.0
            
        # Return average queue size over recent history as percentage of bandwidth
        recent_traffic = [traffic for _, traffic in self.traffic_history[-10:]]
        avg_traffic = sum(recent_traffic) / len(recent_traffic) if recent_traffic else 0
        return min(1.0, avg_traffic / self.bandwidth)
        
    def optimize_routing(self):
        """Optimize routing based on traffic patterns and congestion."""
        # Identify most congested routes
        congested_routes = sorted(self.congestion_points.items(), 
                                 key=lambda x: x[1], 
                                 reverse=True)[:5]
                                 
        # For each congested route, try to find alternative paths
        for route, _ in congested_routes:
            source_id, target_id = route.split('->')
            
            # Find all possible intermediate nodes
            intermediate_candidates = []
            for mid in self.connections:
                # Check if we can go from source to mid and from mid to target
                if (mid != source_id and mid != target_id and
                    any(t[0] == mid for t in self.connections[source_id]) and
                    any(t[0] == target_id for t in self.connections[mid])):
                    intermediate_candidates.append(mid)
                    
            # If we found alternatives, strengthen those routes
            for mid in intermediate_candidates:
                # Increase priority for the alternative route
                for i, (target, priority) in enumerate(self.connections[source_id]):
                    if target == mid:
                        self.connections[source_id][i] = (target, priority * 1.1)
                        
                for i, (target, priority) in enumerate(self.connections[mid]):
                    if target == target_id:
                        self.connections[mid][i] = (target, priority * 1.1)

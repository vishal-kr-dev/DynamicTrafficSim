import os
import sys
import traci
import subprocess
import numpy as np
import xml.etree.ElementTree as ET

class SumoEnvironment:
    
    def __init__(self, use_gui=False, simulation_step=10):
        """
            use_gui: Whether to show SUMO GUI (slower but good for debugging)
            simulation_step: Seconds per simulation step (larger = fas ter)
        """
        self.use_gui = use_gui
        self.simulation_step = simulation_step
        
        # Check SUMO installation
        if 'SUMO_HOME' in os.environ:
            tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
            sys.path.append(tools)
            self.sumo_binary = os.path.join(
                os.environ['SUMO_HOME'], 'bin', 
                'sumo-gui' if use_gui else 'sumo'
            )
        else:
            sys.exit("❌ Please declare environment variable 'SUMO_HOME'")
        
        # --- State and action spaces ---
        self.state_size = 3  # NS_queue_level, EW_queue_level, current_phase
        self.action_size = 2  # 0=KEEP, 1=SWITCH
        
        # Traffic signal control
        self.junction_id = "J0"
        self.current_phase = 0  # 0=NS_green, 1=EW_green
        self.phase_duration = 0
        self.min_phase_duration = 20  # Minimum green time (seconds)
        self.max_phase_duration = 120  # Maximum green time (seconds)
        self.yellow_duration = 4  # Yellow light duration
        self.is_yellow = False
        self.yellow_timer = 0
        
        # --- UPDATED: Discrete state buckets for Q-learning ---
        self.queue_buckets = [0, 3, 8]  # LOW: 0-2, MEDIUM: 3-7, HIGH: 8+
        
        # Performance tracking
        self.total_wait_time = 0
        self.total_vehicles = 0
        
        # File paths
        self.files_dir = "sumo_files"
        self._create_sumo_files()
        
        print(f"🏗️ SUMO Environment initialized:")
        print(f"   Simulation step: {simulation_step}s")
        print(f"   State size: {self.state_size}")
        print(f"   Action size: {self.action_size}")
        print(f"   Use GUI: {use_gui}")
    
    def _create_sumo_files(self):
        """Create all necessary SUMO configuration files."""
        if not os.path.exists(self.files_dir):
            os.makedirs(self.files_dir)
        
        self._create_network_file()
        self._create_traffic_file()
        self._create_config_file()
        self._create_detector_file()
        
        print(f"📁 SUMO files created in {self.files_dir}/")
    
    def _create_network_file(self):
        """Create a simple 4-way intersection network."""
        net_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<net version="1.20" junctionCornerDetail="5" limitTurnSpeed="5.50" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/net_file.xsd">

    <location netOffset="100.00,100.00" convBoundary="0.00,0.00,200.00,200.00" origBoundary="-10000000000.00,-10000000000.00,10000000000.00,10000000000.00" projParameter="!"/>

    <!-- Edges -->
    <edge id="n_to_center" from="n" to="center" priority="2">
        <lane id="n_to_center_0" index="0" speed="13.89" length="100.00" shape="100.00,200.00 100.00,103.20"/>
    </edge>
    
    <edge id="center_to_s" from="center" to="s" priority="2">
        <lane id="center_to_s_0" index="0" speed="13.89" length="100.00" shape="100.00,96.80 100.00,0.00"/>
    </edge>
    
    <edge id="e_to_center" from="e" to="center" priority="2">
        <lane id="e_to_center_0" index="0" speed="13.89" length="100.00" shape="200.00,100.00 103.20,100.00"/>
    </edge>
    
    <edge id="center_to_w" from="center" to="w" priority="2">
        <lane id="center_to_w_0" index="0" speed="13.89" length="100.00" shape="96.80,100.00 0.00,100.00"/>
    </edge>

    <!-- Junctions -->
    <junction id="center" type="traffic_light" x="100.00" y="100.00" incLanes="n_to_center_0 e_to_center_0" intLanes=":center_0_0 :center_1_0" shape="96.80,103.20 103.20,103.20 103.20,96.80 96.80,96.80">
        <request index="0" response="00" foes="10" cont="0"/>
        <request index="1" response="01" foes="01" cont="0"/>
    </junction>
    
    <junction id="n" type="dead_end" x="100.00" y="200.00" incLanes="" intLanes="" shape="101.60,200.00 98.40,200.00"/>
    <junction id="s" type="dead_end" x="100.00" y="0.00" incLanes="center_to_s_0" intLanes="" shape="98.40,0.00 101.60,0.00"/>
    <junction id="e" type="dead_end" x="200.00" y="100.00" incLanes="" intLanes="" shape="200.00,98.40 200.00,101.60"/>
    <junction id="w" type="dead_end" x="0.00" y="100.00" incLanes="center_to_w_0" intLanes="" shape="0.00,101.60 0.00,98.40"/>

    <!-- Internal lanes -->
    <junction id=":center_0" type="internal" x="100.00" y="100.00" incLanes="n_to_center_0" intLanes=":center_1_0" shape="100.00,103.20 100.00,96.80 103.20,96.80"/>
    <junction id=":center_1" type="internal" x="100.00" y="100.00" incLanes="e_to_center_0" intLanes=":center_0_0" shape="103.20,100.00 96.80,100.00 96.80,103.20"/>

    <!-- Traffic light logics -->
    <tlLogic id="J0" type="static" programID="0" offset="0">
        <phase duration="60" state="GO"/>  <!-- NS green, EW red -->
        <phase duration="4" state="yO"/>   <!-- NS yellow, EW red -->
        <phase duration="60" state="OG"/>  <!-- NS red, EW green -->
        <phase duration="4" state="Oy"/>   <!-- NS red, EW yellow -->
    </tlLogic>

    <!-- Connections -->
    <connection from="n_to_center" to="center_to_s" fromLane="0" toLane="0" via=":center_0_0" tl="J0" linkIndex="0" dir="s" state="O"/>
    <connection from="e_to_center" to="center_to_w" fromLane="0" toLane="0" via=":center_1_0" tl="J0" linkIndex="1" dir="s" state="O"/>
    <connection from=":center_0" to="center_to_s" fromLane="0" toLane="0" dir="s" state="M"/>
    <connection from=":center_1" to="center_to_w" fromLane="0" toLane="0" dir="s" state="M"/>
</net>"""
        
        with open(f"{self.files_dir}/intersection.net.xml", 'w') as f:
            f.write(net_xml)
    
    def _create_traffic_file(self):
        """Create optimized traffic demand file with consistent flow."""
        # --- UPDATED: Pre-generated traffic for consistent training ---
        routes_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">
    
    <!-- Vehicle types -->
    <vType id="car" accel="2.0" decel="4.5" length="5.0" maxSpeed="50.0" sigma="0.5"/>
    
    <!-- Routes -->
    <route id="north_to_south" edges="n_to_center center_to_s"/>
    <route id="east_to_west" edges="e_to_center center_to_w"/>
    
    <!-- Traffic flows - consistent demand every simulation -->"""
        
        # Generate consistent traffic pattern
        vehicle_id = 0
        for time in range(0, 600, 15):  # Vehicle every 15 seconds
            # North-South traffic (slightly heavier in morning pattern)
            if vehicle_id % 3 != 2:  # 2/3 of vehicles
                routes_xml += f'\n    <vehicle id="ns_{vehicle_id}" type="car" route="north_to_south" depart="{time}"/>'
            
            # East-West traffic
            if vehicle_id % 4 == 0:  # 1/4 of vehicles
                routes_xml += f'\n    <vehicle id="ew_{vehicle_id}" type="car" route="east_to_west" depart="{time + 5}"/>'
            
            vehicle_id += 1
        
        routes_xml += "\n</routes>"
        
        with open(f"{self.files_dir}/intersection.rou.xml", 'w') as f:
            f.write(routes_xml)
    
    def _create_config_file(self):
        """Create SUMO configuration file."""
        config_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">
    <input>
        <net-file value="intersection.net.xml"/>
        <route-files value="intersection.rou.xml"/>
        <additional-files value="detectors.add.xml"/>
    </input>
    
    <output>
        <summary-output value="summary.xml"/>
    </output>
    
    <time>
        <begin value="0"/>
        <end value="3600"/>
        <step-length value="{self.simulation_step}"/>
    </time>
    
    <processing>
        <ignore-route-errors value="true"/>
        <time-to-teleport value="300"/>
    </processing>
    
    <report>
        <xml-validation value="never"/>
        <no-warnings value="true"/>
        <no-step-log value="true"/>
    </report>
</configuration>"""
        
        with open(f"{self.files_dir}/intersection.sumocfg", 'w') as f:
            f.write(config_xml)
    
    def _create_detector_file(self):
        """Create lane detectors for measuring traffic."""
        # --- UPDATED: Simplified detector setup ---
        detectors_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">
    
    <!-- Lane area detectors for queue measurement -->
    <laneAreaDetector id="det_ns" lane="n_to_center_0" pos="0" endPos="100" file="detector_ns.xml"/>
    <laneAreaDetector id="det_ew" lane="e_to_center_0" pos="0" endPos="100" file="detector_ew.xml"/>
    
</additional>"""
        
        with open(f"{self.files_dir}/detectors.add.xml", 'w') as f:
            f.write(detectors_xml)
    
    def _start_simulation(self):
        """Start SUMO simulation."""
        sumo_cmd = [
            self.sumo_binary,
            "-c", f"{self.files_dir}/intersection.sumocfg",
            "--no-warnings", "true",
            "--no-step-log", "true",
            "--time-to-teleport", "300",
            "--step-length", str(self.simulation_step)
        ]
        
        if self.use_gui:
            sumo_cmd.extend(["--start", "--quit-on-end"])
        
        traci.start(sumo_cmd)
        
        # --- UPDATED: Initialize traffic light to known state ---
        self.current_phase = 0  # Start with NS green
        self.phase_duration = 0
        self.is_yellow = False
        self.yellow_timer = 0
        traci.trafficlight.setPhase(self.junction_id, 0)  # NS green
    
    def reset(self):
        """Reset environment for new episode."""
        if traci.isLoaded():
            traci.close()
        
        self._start_simulation()
        
        # Reset tracking variables
        self.total_wait_time = 0
        self.total_vehicles = 0
        
        # Get initial state
        initial_state = self._get_state()
        return initial_state
    
    def step(self, action):
        """
        Execute one step in the environment.
        
        Args:
            action: 0=KEEP current phase, 1=SWITCH to next phase
        
        Returns:
            tuple: (next_state, reward, total_wait_time)
        """
        # --- UPDATED: Handle yellow light timing ---
        if self.is_yellow:
            self.yellow_timer += 1
            if self.yellow_timer >= (self.yellow_duration // self.simulation_step):
                # Yellow finished, switch to next phase
                self.current_phase = 1 - self.current_phase
                self.is_yellow = False
                self.yellow_timer = 0
                self.phase_duration = 0
                
                # Set new green phase
                new_phase = 0 if self.current_phase == 0 else 2  # 0=NS green, 2=EW green
                traci.trafficlight.setPhase(self.junction_id, new_phase)
        else:
            self.phase_duration += 1
            
            # Handle action if not in yellow and minimum time passed
            if (action == 1 and 
                self.phase_duration >= (self.min_phase_duration // self.simulation_step)):
                # Start yellow phase
                self.is_yellow = True
                self.yellow_timer = 0
                yellow_phase = 1 if self.current_phase == 0 else 3  # 1=NS yellow, 3=EW yellow
                traci.trafficlight.setPhase(self.junction_id, yellow_phase)
            
            # Force switch if maximum time reached
            elif self.phase_duration >= (self.max_phase_duration // self.simulation_step):
                self.is_yellow = True
                self.yellow_timer = 0
                yellow_phase = 1 if self.current_phase == 0 else 3
                traci.trafficlight.setPhase(self.junction_id, yellow_phase)
        
        # Advance simulation
        traci.simulationStep()
        
        # Get new state and calculate reward
        new_state = self._get_state()
        reward = self._calculate_reward()
        
        # Track total wait time for episode statistics
        current_wait = self._get_total_wait_time()
        self.total_wait_time = current_wait
        
        return new_state, reward, current_wait
    
    def _get_state(self):
        """
        Get current state representation.
        
        Returns:
            numpy.array: [NS_queue_bucket, EW_queue_bucket, current_phase]
        """
        try:
            # Get queue lengths
            ns_queue = traci.lanearea.getLastStepHaltingNumber("det_ns")
            ew_queue = traci.lanearea.getLastStepHaltingNumber("det_ew")
            
            # --- UPDATED: Convert to discrete buckets for  Q-learning ---
            ns_bucket = self._queue_to_bucket(ns_queue)
            ew_bucket = self._queue_to_bucket(ew_queue)
            
            state = np.array([ns_bucket, ew_bucket, self.current_phase], dtype=int)
            return state
            
        except traci.TraCIException:
            # Return safe default state if measurement fails
            return np.array([0, 0, 0], dtype=int)
    
    def _queue_to_bucket(self, queue_length):
        """Convert queue length to discrete bucket."""
        if queue_length <= self.queue_buckets[1]:
            return 0  # LOW
        elif queue_length <= self.queue_buckets[2]:
            return 1  # MEDIUM
        else:
            return 2  # HIGH
    
    def _calculate_reward(self):
        """
        Calculate reward based on traffic performance.
        
        Returns:
            float: Reward value (negative for bad performance)
        """
        try:
            # Get current queue lengths
            ns_queue = traci.lanearea.getLastStepHaltingNumber("det_ns")
            ew_queue = traci.lanearea.getLastStepHaltingNumber("det_ew")
            
            # --- UPDATED: Simple reward function for  training ---
            total_queue = ns_queue + ew_queue
            
            # Penalize long queues, reward empty intersections
            if total_queue == 0:
                reward = 2.0  # Bonus for clear intersection
            elif total_queue <= 3:
                reward = 1.0  # Good performance
            elif total_queue <= 8:
                reward = -1.0  # Moderate congestion
            else:
                reward = -3.0  # Heavy congestion
            
            # Additional penalty for very unbalanced traffic
            queue_imbalance = abs(ns_queue - ew_queue)
            if queue_imbalance > 5:
                reward -= 1.0
            
            return reward
            
        except traci.TraCIException:
            return 0.0  # Neutral reward if measurement fails
    
    def _get_total_wait_time(self):
        """Get total waiting time of all vehicles."""
        try:
            total_wait = 0
            vehicle_ids = traci.vehicle.getIDList()
            
            for vid in vehicle_ids:
                wait_time = traci.vehicle.getWaitingTime(vid)
                total_wait += wait_time
            
            return total_wait
            
        except traci.TraCIException:
            return 0.0
    
    def get_state_size(self):
        """Get the size of the state space."""
        return self.state_size
    
    def get_action_size(self):
        """Get the size of the action space."""
        return self.action_size
    
    def close(self):
        """Clean up and close SUMO simulation."""
        if traci.isLoaded():
            traci.close()
        print("🔄 SUMO simulation closed")
    
    def render_state_info(self):
        """Print current state information (for debugging)."""
        try:
            state = self._get_state()
            ns_queue = traci.lanearea.getLastStepHaltingNumber("det_ns")
            ew_queue = traci.lanearea.getLastStepHaltingNumber("det_ew")
            
            phase_name = "NS Green" if self.current_phase == 0 else "EW Green"
            if self.is_yellow:
                phase_name += " (Yellow)"
            
            print(f"State: NS={state[0]} ({ns_queue}), EW={state[1]} ({ew_queue}), Phase={phase_name}")
            
        except traci.TraCIException:
            print("State information unavailable")
    
    def get_performance_metrics(self):
        """Get current performance metrics."""
        try:
            # Vehicle metrics
            vehicle_ids = traci.vehicle.getIDList()
            total_vehicles = len(vehicle_ids)
            
            if total_vehicles > 0:
                total_wait = sum(traci.vehicle.getWaitingTime(vid) for vid in vehicle_ids)
                avg_wait = total_wait / total_vehicles
            else:
                total_wait = 0
                avg_wait = 0
            
            # Queue metrics
            ns_queue = traci.lanearea.getLastStepHaltingNumber("det_ns")
            ew_queue = traci.lanearea.getLastStepHaltingNumber("det_ew")
            total_queue = ns_queue + ew_queue
            
            return {
                'total_vehicles': total_vehicles,
                'total_wait_time': total_wait,
                'avg_wait_time': avg_wait,
                'ns_queue': ns_queue,
                'ew_queue': ew_queue,
                'total_queue': total_queue,
                'current_phase': self.current_phase,
                'phase_duration': self.phase_duration * self.simulation_step
            }
            
        except traci.TraCIException:
            return {
                'total_vehicles': 0,
                'total_wait_time': 0,
                'avg_wait_time': 0,
                'ns_queue': 0,
                'ew_queue': 0,
                'total_queue': 0,
                'current_phase': self.current_phase,
                'phase_duration': 0
            }
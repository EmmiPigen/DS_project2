#! /usr/bin/env python3

# src/main.py

# script to run the simulation and nodes
#autopep8: off
import sys
sys.dont_write_bytecode = True  # Prevent creation of .pyc files
#autopep8: off

import os
from platform import node
import time
import threading
# autopep8: off
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.networkSimulation import networkSimulator
from src.eventLogger import EventLogger
from src.Lamport_timestamps.node import LamportNode
from src.Vector_clocks.node import VectorClockNode
# autopep8: on


class SimulationManager:
  def __init__(self, num_nodes, NODE_TYPE="LAMPORT"):
    # Initialize logger and network simulator
    self.sim_manager = networkSimulator(num_nodes)
    self.logger = EventLogger(f"simulationLog_{NODE_TYPE}.txt")
    self.nodes = []
    self.NODE_TYPE = NODE_TYPE

    self.setup_nodes(num_nodes)

  def setup_nodes(self, num_nodes):
    # Start Nodes of the specified type
    if self.NODE_TYPE == "LAMPORT":
      NodeClass = LamportNode
    elif self.NODE_TYPE == "VECTOR":
      NodeClass = VectorClockNode

    for node_id in range(1, num_nodes + 1):
      known_nodes = list(range(1, num_nodes + 1))
      node = NodeClass(node_id, known_nodes, self.logger)
      threading.Thread(target=node.start, daemon=True).start()
      self.nodes.append(node)
      time.sleep(0.5)  # Stagger node startups


if __name__ == "__main__":
  # If NODE_TYPE is specified, use it, else default to LAMPORT
  if len(sys.argv) > 2:  # Should be the second arg
    NODE_TYPE = sys.argv[2].upper()  # takes the second argument
  else:
    NODE_TYPE = "LAMPORT"

  NUM_NODES = int(sys.argv[1])  # First argument is number of nodes
  print(f"Starting simulation with {NUM_NODES} nodes of type {NODE_TYPE}")
  sim_manager = SimulationManager(NUM_NODES, NODE_TYPE)

  # Allow for terminal interaction
  try:
    while True:
      cmd = input("Enter command: ").lower().strip().split()

      if cmd[0] == "status":
        node_id = int(cmd[1]) - 1
        print(f"Status of Node {node_id}:")
        sim_manager.nodes[node_id].status()

      if cmd[0] == "request":  # Sent a request for entry into critical section
        node_id = int(cmd[1])
        target_id = int(cmd[2])

        print(f"Node {node_id} requesting access to critical section from Node {target_id}")

        message = sim_manager.nodes[node_id - 1]._create_message(target_id, "REQUEST")
        sim_manager.nodes[node_id - 1].send_message(target_id, message)

      if cmd[0] == "contact":  # for sending a contact message
        node_id = int(cmd[1])
        target_id = int(cmd[2])

        print(f"Node {node_id} contacting Node {target_id}")

        message = sim_manager.nodes[node_id - 1]._create_message(target_id, "CONTACT")
        sim_manager.nodes[node_id - 1].send_message(target_id, message)
      time.sleep(3)  # Small delay to allow message processing

  except KeyboardInterrupt:
    print("\nShutting down simulation.")

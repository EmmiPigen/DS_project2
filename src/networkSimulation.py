#!/usr/bin/env python3

# src/SimulationManager.py

# This is the main simulation manager that holds the processes and handles the communication and an event logger for analyzing the results of the simulation.

import socket
import threading
import time
import sys
import random
import json

SIM_PORT = 5000
NODE_PORT_BASE = 6000
MIN_DELAY = 0.5
MAX_DELAY = 1.0


class networkSimulator:
  def __init__(self, numNodes, minDelay=MIN_DELAY, maxDelay=MAX_DELAY):
    # Initialize simulation manager with the node objects and an event logger
    self.numNodes = numNodes
    self.minDelay = minDelay
    self.maxDelay = maxDelay

    self.messageQueue = []
    self.queueLock = threading.Lock()

    threading.Thread(target=self.listen, daemon=True).start()
    threading.Thread(target=self.deliver_messages, daemon=True).start()

    print(
        f"Network Simulator is running on Port {SIM_PORT} with {self.numNodes} nodes.")

  def listen(self):
    """Listens and receives incoming messages from nodes."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
      server.bind(("localhost", SIM_PORT))
      server.listen()
    except OSError as e:
      print(f"Error starting network simulator: {e}")
      return

    server.settimeout(1.0)

    while True:
      try:
        conn, _ = server.accept()
        raw_data = conn.recv(1024).decode("utf-8")
        conn.close()
        self.schedule_delivery(raw_data)
      except socket.timeout:
        continue
      except Exception as e:
        print(f"Simulation manager listener error: {e}")
        continue

  def schedule_delivery(self, message):
    """Schedules a message for delivery after a random delay."""
    try:
      msg_data = json.loads(message)

      delay = random.uniform(self.minDelay, self.maxDelay)
      delivery_time = time.time() + delay

      with self.queueLock:
        self.messageQueue.append(
            {
                "message": message,
                "target_id": msg_data["receiver_id"],
                "delivery_time": delivery_time
            }
        )
        self.messageQueue.sort(key=lambda x: x["delivery_time"])

    except json.JSONDecodeError:
      print(f"[SYSTEM] Failed to decode message: {message}")
    except Exception as e:
      print(f"[SYSTEM] Error scheduling delivery: {e}")

  def deliver_messages(self):
    """Delivers messages to their target nodes after the scheduled delay."""
    while True:
      now = time.time()
      delivered_messages = []

      with self.queueLock:
        for i, msg in enumerate(self.messageQueue):
          if msg["delivery_time"] <= now:
            threading.Thread(target=self._forward_message, args=(msg,), daemon=True).start()
            delivered_messages.append(i)
          else:
            break

        for index in sorted(delivered_messages, reverse=True):
          del self.messageQueue[index]

          time.sleep(0.1)

  def _forward_message(self, msg):
    """Forwards the message to the target node."""
    target_id = msg["target_id"]
    target_port = NODE_PORT_BASE + target_id
    msg_data = json.loads(msg["message"])

    try:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect(("localhost", target_port))
      s.sendall(msg["message"].encode("utf-8"))
      s.close()
      # print(f"[DELIVERED] {msg_data['msg_type']} to node {target_id}.")
    except (ConnectionRefusedError, OSError):
      print(f"[FAILED] Could not deliver message to node {target_id}. Node may be down.")

      # Could implement retry logic here if desired

  def shutdown(self):
    """Shuts down the network simulator."""
    sys.exit(0)

if __name__ == "__main__":
  if len(sys.argv) < 2:
    print("Usage: python networkSimulation.py <num_nodes> [<min_delay>] [<max_delay>]")  # min_delay and max_delay are optional
    sys.exit(1)

  num_nodes = int(sys.argv[1])  # Number of nodes in the simulation
  min_delay = float(sys.argv[2]) if len(sys.argv) > 2 else MIN_DELAY
  max_delay = float(sys.argv[3]) if len(sys.argv) > 3 else MAX_DELAY
  sim_manager = networkSimulator(num_nodes, min_delay, max_delay)

  if sim_manager:
    try:
      while True:
        time.sleep(1)
    except KeyboardInterrupt:
      print("Simulation Manager shutting down.")
      sys.exit(0)

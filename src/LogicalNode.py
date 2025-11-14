#!/usr/bin python3

# src/LogicalNode.py

# Abstract LogicalNode class representing to build the Lamport timestamp and vector clock nodes upon.
from abc import ABC, abstractmethod
import socket
import sys
import threading
import json

from regex import D

from src.networkSimulation import SIM_PORT, NODE_PORT_BASE


class LogicalNode(ABC):
  def __init__(self, node_Id, known_Nodes, logger):
    self.node_Id = node_Id
    self.known_Nodes = known_Nodes
    self.PORT_BASE = NODE_PORT_BASE
    self.logger = logger  # Logger class to log events
    self.request_queue = []
    self.is_in_critical_section = False
    self.is_alive = True

    self._status = "IDLE"
    self.message_Queue = []
    self.queue_Lock = threading.Lock()
    self.state_Lock = threading.Lock()

  def start(self):
    self.listener_thread = threading.Thread(target=self.listen, daemon=True)
    self.processor_thread = threading.Thread(target=self.process_message, daemon=True)
    self.listener_thread.start()
    self.processor_thread.start()

  @abstractmethod
  def listen(self):
    pass

  @abstractmethod
  def process_message(self):
    pass

  def handle_message(self, msg):
    """Handles the received messages based on their type."""
    if msg.msg_type == "CONTACT":
      print(f"Node {self.node_Id} received CONTACT from Node {msg.sender_id}")

    else:
      print(f"Node {self.node_Id} received unknown message type: {msg.msg_type}")

  @abstractmethod
  def _create_message(self, target_Id, message_type):
    pass

  def send_message(self, targetId, message):
    try:
      self.logger.record_event(self.node_Id, "SEND_MESSAGE",
                               getattr(self, 'lamport_Clock', getattr(self, 'vector_Clock', None)),
                               details=f"Sent {message.msg_type} to Node {targetId}")
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect(("localhost", SIM_PORT))

      s.sendall(json.dumps(message.to_dict()).encode("utf-8"))
      s.close()
      self._status = "IDLE"

      print(f"Node {self.node_Id} sent {message.msg_type} to Node {targetId}.")

    except (ConnectionRefusedError, OSError):
      print(f"Node {self.node_Id} failed to send message to Node {targetId}. Simulator may be down.")

  @abstractmethod
  def local_event(self):
    pass

  @abstractmethod
  def stop(self):
    pass

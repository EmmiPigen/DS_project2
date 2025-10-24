#!/usr/bin python3

# src/LogicalNode.py

# Abstract LogicalNode class representing to build the Lamport timestamp and vector clock nodes upon.
from abc import ABC, abstractmethod
import socket
import threading

from src.simulationManager import SIM_PORT, NODE_PORT_BASE


class LogicalNode(ABC):
  def __init__(self, node_Id, known_Nodes):
    self.node_Id = node_Id
    self.known_Nodes = known_Nodes
    self.PORT_BASE = NODE_PORT_BASE

    self.status = "IDLE"
    self.message_Queue = []
    self.queue_Lock = threading.Lock()
    self.state_Lock = threading.Lock()

    threading.Thread(target=self.listen, daemon=True).start()
    threading.Thread(target=self.process_message, daemon=True).start()

  @abstractmethod
  def listen(self):
    pass

  @abstractmethod
  def process_message(self):
    pass

  @abstractmethod
  def handle_message(self, message):
    pass

  def send_message(self, targetId, message):
    try:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect(("localhost", SIM_PORT))

      s.sendall(message.encode("utf-8"))
      s.close()

      print(f"Node {self.node_Id} sent {message.msg_type} to Node {targetId}.")

    except (ConnectionRefusedError, OSError):
      print(f"Node {self.node_Id} failed to send message to Node {targetId}. Simulator may be down.")

  @abstractmethod
  def local_event(self):
    pass

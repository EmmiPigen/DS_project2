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

  def listen(self):
    """Listens and receives incoming messages from other nodes via the simulator."""
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("localhost", self.PORT_BASE + self.node_Id))
    server.listen()
    server.settimeout(1.0)
    
    print(f"Node {self.node_Id} listening on port {self.PORT_BASE + self.node_Id}")
    
    while True:
      try:
        conn, _ = server.accept()
        raw_data = conn.recv(1024).decode("utf-8")
        print("Message:", raw_data)
        conn.close()
        with self.queue_Lock:
          self.message_Queue.append(raw_data)
      except socket.timeout:
        continue
            
  @abstractmethod
  def process_message(self):
    pass

  @abstractmethod
  def handle_message(self, message):
    pass
  
  def broadcast(self, message):
    print(f"Node {self.node_Id} broadcasting {message.msg_type} to all known nodes.")
    for target_Id in self.known_Nodes:
      if target_Id != self.node_Id:
        target_message = self._create_message(target_Id, message.msg_type)
        self.send_message(target_Id, target_message)
        
  @abstractmethod
  def _create_message(self, target_Id, message_type):
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

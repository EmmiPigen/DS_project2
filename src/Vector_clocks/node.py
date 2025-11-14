#!/usr/bin python3

# src/vector_clocks/node.py
import sys
import socket
import json
import struct
import binascii

# autopep8: off
from src.LogicalNode import LogicalNode
from src.Vector_clocks.vectorMessage import VectorMessage

# autopep8: on

class VectorClockNode(LogicalNode):
  def __init__(self, node_Id, known_Nodes, logger):
    self.vector_Clock = [0] * len(known_Nodes)  # Initialize vector clock
    super().__init__(node_Id, known_Nodes, logger)

  def listen(self):
    """Listens for incoming messages and appends them to the message queue."""
    self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.server.bind(("localhost", self.PORT_BASE + self.node_Id))
    self.server.listen()
    self.server.settimeout(1.0)

    print(f"Node {self.node_Id} listening on port {self.PORT_BASE + self.node_Id}")

    while self.is_alive:
      try:
        conn, _ = self.server.accept()
        msg = json.loads(conn.recv(1024).decode("utf-8"))
        conn.close()
        hex_clock = msg['vector_clock']
        raw_clock = binascii.unhexlify(hex_clock.encode('utf-8'))
        num_nodes = len(raw_clock) // 4
        vector_clock = list(struct.unpack('!' + 'I' * num_nodes, raw_clock))

        msg_obj = VectorMessage(msg['msg_type'], msg['sender_id'], msg['receiver_id'], vector_clock)
        with self.queue_Lock:
          self._status = "RECEIVING"
          self.message_Queue.append(msg_obj)
          self._status = "IDLE"
      except socket.timeout:
        continue

  def process_message(self):
    """Allows the node to process incoming messages and update vector clock."""
    while True:
      msg = None  # reset msg to None before acquiring lock
      with self.queue_Lock:
        if self.message_Queue:
          msg = self.message_Queue.pop(0)  # Get the first message in the queue
      if msg:
        self._status = "RECEIVING"
        with self.state_Lock:
          # Update vector clock
          self.vector_Clock = [max(vc1, vc2) for vc1, vc2 in zip(self.vector_Clock, msg.vector_clock)]
          self.vector_Clock[self.node_Id - 1] += 1  # Increment own entry

          # Log the event in the logger
          self.logger.record_event(self.node_Id, "RECEIVE_MESSAGE", self.vector_Clock.copy(), details=f"Received {msg.msg_type} from Node {msg.sender_id}")

          print(f"Node {self.node_Id} updated vector clock to {self.vector_Clock} after receiving message from Node {msg.sender_id}")
          self.handle_message(msg)
          self._status = "IDLE"

  def local_event(self):
    """Simulates a local event(non-communication event) and increments vector clock."""
    print(f"Node {self.node_Id} performing local event.")
    with self.state_Lock:
      self._status = "LOCAL_EVENT"
      self.vector_Clock[self.node_Id - 1] += 1
      print(f"Node {self.node_Id} incremented its vector clock to {self.vector_Clock} for local event.")
      self.logger.record_event(self.node_Id, "LOCAL_EVENT", self.vector_Clock.copy())
      self._status = "IDLE"

  def _create_message(self, target_Id, message_type):
    """Creates a VectorMessage with the current vector clock."""
    with self.state_Lock:
      self._status = "SENDING"
      self.vector_Clock[self.node_Id - 1] += 1  # Increment own entry
      print(f"Node {self.node_Id} incremented its vector clock to {self.vector_Clock} for sending message.")
      return VectorMessage(message_type, self.node_Id, target_Id, self.vector_Clock.copy())

  def status(self):
    """Helper method to print the current status of the node."""
    print(f" \
              Node {self.node_Id} \n \
              Known Nodes: {self.known_Nodes} \n \
              Vector Clock: {self.vector_Clock} \n \
              Status: {self._status}")
    
  def stop(self):
    """Stops the node's operations."""
    try:
      self.server.shutdown(socket.SHUT_RDWR)
      self.server.close()
    except Exception as e:
      pass
    

if __name__ == "__main__":
  if len(sys.argv) != 3:
    print("Usage: python node.py <node_id> <known_nodes>")
    sys.exit(1)

  node_id = int(sys.argv[1])
  known_nodes = list(range(1, int(sys.argv[2]) + 1))  # Assuming known nodes are numbered from 1 to N

  node = VectorClockNode(node_id, known_nodes, None)

  try:
    while True:
      full_cmd = input(f"Node {node_id} > ").strip().split()

      if not full_cmd:
        continue

      cmd = full_cmd[0].lower()

      if cmd == "status":
        print(f" \
              Node {node.node_Id} \n \
              Known Nodes: {node.known_Nodes} \n \
              Vector Clock: {node.vector_Clock} \n \
              Status: {node._status}")

      elif cmd == "contact":
        if len(full_cmd) < 2 or not full_cmd[1].isdigit():
          print("Usage: contact <target_node_id>")
          continue

        try:
          target_id = int(full_cmd[1])
          node.send_message(target_id, "CONTACT")
        except ValueError:
          print("Invalid target node ID.")

      elif cmd == "exit":
        print(f"Shutting down Node {node.node_Id}.")
        break

  except KeyboardInterrupt:
    print(f"\nShutting down Node {node.node_Id}.")

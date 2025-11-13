#!/usr/bin python3

# src/Lamport_timestamps/node.py
import sys
import socket
import json

# autopep8: off
from src.LogicalNode import LogicalNode
from src.Lamport_timestamps.lamportMessage import LamportMessage

# autopep8: on


class LamportNode(LogicalNode):
  def __init__(self, node_Id, known_Nodes, logger):
    self.lamport_Clock = 0  # Initialize Lamport clock
    super().__init__(node_Id, known_Nodes, logger)


  def listen(self):
    """Listens for incoming messages and appends them to the message queue."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("localhost", self.PORT_BASE + self.node_Id))
    server.listen()
    server.settimeout(1.0)

    print(f"Node {self.node_Id} listening on port {self.PORT_BASE + self.node_Id}")

    while True:
      try:
        conn, _ = server.accept()
        msg = json.loads(conn.recv(1024).decode("utf-8"))
        conn.close()
        msg_obj = LamportMessage(msg['msg_type'], msg['sender_id'], msg['receiver_id'], msg['timestamp'])
        with self.queue_Lock:
          self.message_Queue.append(msg_obj)
      except socket.timeout:
        continue

  def process_message(self):
    """Allows the node to process incoming messages and update Lamport clock."""
    while True:
      msg = None  # reset msg to None before acquiring lock
      with self.queue_Lock:
        if self.message_Queue:
          msg = self.message_Queue.pop(0)  # Get the first message in the queue
      if msg:
        with self.state_Lock:
          # Update Lamport clock following Lamport's rules: C = max(C, T) + 1
          self.lamport_Clock = max(self.lamport_Clock, msg.timestamp) + 1
          self.logger.record_event(self.node_Id, "RECEIVE_MESSAGE", self.lamport_Clock, details=f"Received {msg.msg_type} from Node {msg.sender_id}")

          print(f"Node {self.node_Id} updated Lamport clock to {self.lamport_Clock} after receiving message from Node {msg.sender_id}")
          self.handle_message(msg)

  def local_event(self):
    """Simulates a local event(non-communication event) and increments Lamport clock."""
    print(f"Node {self.node_Id} performing local event.")
    with self.state_Lock:
      self.lamport_Clock += 1
      self.logger.record_event(self.node_Id, "LOCAL_EVENT", self.lamport_Clock)

  def _create_message(self, target_Id, message_type):
    """Creates a LamportMessage with the current Lamport clock."""
    with self.state_Lock:
      self.lamport_Clock += 1
      print(f"Node {self.node_Id} incremented Lamport clock to {self.lamport_Clock} for sending message.")
      return LamportMessage(message_type, self.node_Id, target_Id, self.lamport_Clock)

  def status(self):
    print(f" \
              Node {self.node_Id} \n \
              Known Nodes: {self.known_Nodes} \n \
              Lamport Clock: {self.lamport_Clock} \n \
              Status: {self._status}")


if __name__ == "__main__":
  if len(sys.argv) != 3:
    print("Usage: python node.py <node_id> <known_nodes>")
    sys.exit(1)

  node_id = int(sys.argv[1])
  known_nodes = list(range(1, int(sys.argv[2]) + 1))  # Assuming known nodes are numbered from 1 to N

  node = LamportNode(node_id, known_nodes, None)

  try:
    while True:
      full_cmd = input(f"Node {node_id} > ").strip().split()

      if not full_cmd:
        continue

      cmd = full_cmd[0].lower()

      if cmd == "status":
        node.status()

      elif cmd == "contact":
        if len(full_cmd) < 2 or not full_cmd[1].isdigit():
          print("Usage: contact <target_node_id>")
          continue

        try:
          target_id = int(full_cmd[1])
          message = node._create_message(target_id, "CONTACT")
          node.send_message(target_id, message)
        except ValueError:
          print("Invalid target node ID.")

      elif cmd == "exit":
        print(f"Shutting down Node {node.node_Id}.")
        break

  except KeyboardInterrupt:
    print(f"\nShutting down Node {node.node_Id}.")

# src/lamportMessage.py

# LamportMessage class for representing messages with Lamport timestamps in a distributed system.

class LamportMessage:
  def __init__(self, msg_type, sender_id, receiver_id, timestamp):  # Constructor for the message class
    self.msg_type = msg_type
    self.sender_id = sender_id
    self.receiver_id = receiver_id
    self.timestamp = timestamp

  def __repr__(self):  # String representation of the message
    return f"[Msg: type={self.msg_type}, N{self.sender_id} -> N{self.receiver_id}, timestamp={self.timestamp}]"

  def __eq__(self, other):  # Equality check for comparing two messages used in testing
    if not isinstance(other, LamportMessage):
      return False
    return (self.sender_id == other.sender_id and
            self.receiver_id == other.receiver_id and
            self.timestamp == other.timestamp and
            self.msg_type == other.msg_type)

  def to_dict(self):
    """Converts the LamportMessage to a dictionary for json encoding."""
    return {
      'msg_type': self.msg_type,
      'sender_id': self.sender_id,
      'receiver_id': self.receiver_id,
      'timestamp': self.timestamp
    }

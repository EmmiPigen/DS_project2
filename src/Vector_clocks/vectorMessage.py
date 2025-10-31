# src/Vector_clocks/vectorMessage.py
# VectorMessage class for representing messages with vector timestamps in a distributed system.

class VectorMessage:
  def __init__(self, msg_type, sender_id, receiver_id, vector_clock):  # Constructor for the message class
    self.msg_type = msg_type
    self.sender_id = sender_id
    self.receiver_id = receiver_id
    self.vector_clock = vector_clock

  def __repr__(self):  # String representation of the message
    return f"[Msg: type={self.msg_type}, N{self.sender_id} -> N{self.receiver_id}, vector_clock={self.vector_clock}]"

  def __eq__(self, other):  # Equality check for comparing two messages used in testing
    if not isinstance(other, VectorMessage):
      return False
    return (self.sender_id == other.sender_id and
            self.receiver_id == other.receiver_id and
            self.vector_clock == other.vector_clock and
            self.msg_type == other.msg_type)

  def to_dict(self):
    """Converts the VectorMessage to a dictionary for json encoding."""
    return {
      'msg_type': self.msg_type,
      'sender_id': self.sender_id,
      'receiver_id': self.receiver_id,
      'vector_clock': self.vector_clock
    }
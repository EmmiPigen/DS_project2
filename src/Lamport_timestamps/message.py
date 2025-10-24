#src/utility/message.py

#Class for the message type uses in the Lamport timestamps implementation

class Message:
  def __init__(self, sender_id, receiver_id, timestamp, content): # Constructor for the message class
    self.sender_id = sender_id
    self.receiver_id = receiver_id
    self.timestamp = timestamp
    self.content = content

  def __repr__(self): # String representation of the message
    return f"[Msg: N{self.sender_id} -> N{self.receiver_id} (TS: {self.timestamp}), Content: {self.content})]"
  
  def __eq__(self, other): # Equality check for comparing two messages used in testing
    if not isinstance(other, Message):
      return False
    return (self.sender_id == other.sender_id and
            self.receiver_id == other.receiver_id and
            self.timestamp == other.timestamp and
            self.content == other.content)

    

    

  
  

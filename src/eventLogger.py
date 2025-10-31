#!/usr/bin python3

# src/eventLogger.py

# Class for logging all event data for analysis after the simulation
import time


class EventLogger:
  def __init__(self, log_file):

    self.log_file = log_file
    
    # Clear existing log file
    with open(self.log_file, "w") as f:
      f.write("")

  def record_event(self, node_id, event_type, clock, details=""):
    timestamp = self.getTime()
    event = f" Node {node_id} - {event_type} (Clock: {clock}) - {details}"
    
    with open(self.log_file, "a") as f:
      f.write(f"{event}\n")


  def getTime(self):
    return time.strftime("%H:%M:%S", time.localtime())

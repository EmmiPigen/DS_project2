#!/usr/bin python3

# src/eventLogger.py

# Class for logging all event data for analysis after the simulation
import time



class EventLogger:
  def __init__(self):
    self.log = []
  
  def record_event(self, node_id, event_type, clock, details=""):
    timestamp = self.getTime()
    event = {
      "timestamp": timestamp,
      "node_id": node_id,
      "event_type": event_type,
      "clock": clock,
      "details": details
    }
    self.log.append(event)
    print(f"[{timestamp}] [LOG] Node {node_id} - {event_type} (Clock: {clock}) {details}")
  
  def get_log(self):
    return self.log

  def getTime(self):
    return time.strftime("%H:%M:%S", time.localtime())
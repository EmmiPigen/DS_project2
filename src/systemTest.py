#!/usr/bin/env python3

# src/systemTest.py

"""
System Test for the Lamport and Vector Clock Implementations
----------------------------------------
Tests correctness of message ordering and overhead analysis
using the real network simulator and Node implementations.
"""


# autopep8: off
import threading
import time
import pytest
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.networkSimulation import networkSimulator
from src.Lamport_timestamps.node import LamportNode
from src.Vector_clocks.node import VectorClockNode
from src.eventLogger import EventLogger
from src.simulationManager import SimulationManager
# autopep8: on

# --- Utility helpers ---------------------------------------------------------


def get_node_by_id(manager, node_id):
  """Helper to retrieve a node object by its ID."""
  return manager.nodes[node_id - 1]


def wait_until(condition_fn, timeout=10, poll=0.5):
  """Waits until condition_fn() returns True or timeout occurs."""
  start = time.time()
  while time.time() - start < timeout:
    if condition_fn():
      return True
    time.sleep(poll)
  return False


def run_scenario(manager, scenario_fn, t=10):
  """Runs a sequence of events defined in the scenario_fn, timeout after t seconds for waiting for idle state."""
  for node_id, event_type, target_id in scenario_fn:
    node = get_node_by_id(manager, node_id)
    if event_type == "LOCAL_EVENT":
      node.local_event()
    elif event_type == "SEND":
      message = node._create_message(target_id, "CONTACT")
      node.send_message(target_id, message)
    time.sleep(1)  # Allow some time between events

  wait_until(lambda: all(n.message_Queue == [] and n._status == "IDLE" for n in manager.nodes), timeout=t)

def get_message_log(log_file_path, length):
  """Verifies that messages were processed in the correct order based on timestamps."""
  events = []
  eid = 0
  with open(log_file_path, 'r') as f:
    logs = [json.loads(line) for line in f.readlines()]
    for log in range(len(logs) - length, len(logs)):
      events.append({
        'eid': eid,
        'node_id': logs[log]['node_id'],
        'event_type': logs[log]['event_type'],
        'clock': logs[log]['clock'],
        'details': logs[log]['details']
      })
      eid += 1
  return events

def verify_message_ordering(events, algorithm):    
  """Verifies that messages were processed in the correct order based on timestamps."""
  # 1. Map Explicit Causal Links (A -> B)
  # This identifies the 'happened-before' relationship established by messages.
  # causal_map = {sender_event_eid: receiver_event_eid, ...}
  causal_map = {}
  
  # Iterate through events to link SEND events to their corresponding RECEIVE events.
  # This requires using the message details (sender ID, receiver ID) to match up
  # the exact pair of events in the log.
  for event in events:
    if event['event_type'] == "SEND_MESSAGE":
      sender_event_eid = event['eid']
      sender_id = event['node_id']
      # Find corresponding RECEIVE event
      for recv_event in events:
        if (recv_event['event_type'] == "RECEIVE_MESSAGE" and
            recv_event['details'].endswith(f"from Node {sender_id}")):
          causal_map[sender_event_eid] = recv_event['eid']
          break
  
  # 2. Verify Clock Orderings
  if algorithm == "LAMPORT":
    for send_eid, recv_eid in causal_map.items():
      send_event = next(e for e in events if e['eid'] == send_eid)
      recv_event = next(e for e in events if e['eid'] == recv_eid)
      if not (send_event['clock'] < recv_event['clock']):
        raise AssertionError(f"Lamport clock violation: SEND event {send_eid} (clock {send_event['clock']}) should be less than RECEIVE event {recv_eid} (clock {recv_event['clock']})")
  elif algorithm == "VECTOR":
    for send_eid, recv_eid in causal_map.items():
      send_event = next(e for e in events if e['eid'] == send_eid)
      recv_event = next(e for e in events if e['eid'] == recv_eid)
      send_clock = send_event['clock']
      recv_clock = recv_event['clock']
      # Vector clock comparison: send_clock < recv_clock
      if not all(s <= r for s, r in zip(send_clock, recv_clock)) or not any(s < r for s, r in zip(send_clock, recv_clock)):
        raise AssertionError(f"Vector clock violation: SEND event {send_eid} (clock {send_clock}) should be less than RECEIVE event {recv_eid} (clock {recv_clock})")
    
  print(f"All messages verified for correct ordering using {algorithm} clocks.")
  return True

# --- Fixtures ----------------------------------------------------------------


@pytest.fixture(params=["LAMPORT", "VECTOR"], scope="module")
def node_setup(request):
  NODE_TYPE = request.param
  NUM_NODES = 4

  manager = SimulationManager(NUM_NODES, NODE_TYPE)
  # Allow some time for nodes to start
  assert wait_until(lambda: len(manager.nodes) == NUM_NODES, timeout=15), "Nodes did not start in time"
  yield manager, NODE_TYPE
  # Teardown logic if needed
  del manager


# --- Tests --------------------------------------------------------------------

def test_startup(node_setup):
  manager, NODE_TYPE = node_setup
  for node in manager.nodes:
    assert node._status == "IDLE", f"Node {node.node_Id} did not start in IDLE state."

def test_message_ordering_simple(node_setup):
  """Test correct ordering of messages in a single send scenario."""
  manager, NODE_TYPE = node_setup

  scenario = [
      (1, "SEND", 2)
  ]
  run_scenario(manager, scenario)

  wait_until(lambda: all(n.message_Queue == [] and n._status == "IDLE" for n in manager.nodes), timeout=10)
  time.sleep(1)  # Ensure logs are flushed
  
  node1 = get_node_by_id(manager, 1)
  node2 = get_node_by_id(manager, 2)
  
  if NODE_TYPE == "LAMPORT":
    assert node1.lamport_Clock == 1, "Node 1 Lamport clock incorrect after sending message."
    assert node2.lamport_Clock == 2, "Node 2 Lamport clock incorrect after receiving message."
  else:  # VECTOR
    assert node1.vector_Clock == [1, 0, 0, 0], "Node 1 Vector clock incorrect after sending message."
    assert node2.vector_Clock == [1, 1, 0, 0], "Node 2 Vector clock incorrect after receiving message."
    
    
def test_message_ordering_sequential(node_setup):
  """
  Test correct ordering of messages in a sequential send scenario.
  Scenario:
    Node 1 sends to Node 2
    Node 2 sends to Node 3
    Node 3 LOCAL_EVENT
    Node 3 sends to Node 4

  Expected: All nodes process messages in the correct order.
  """
  manager, NODE_TYPE = node_setup

  scenario = [
      (1, "SEND", 2),
      (2, "SEND", 3),
      (3, "LOCAL_EVENT", None),
      (3, "SEND", 4),
  ]

  run_scenario(manager, scenario)
  events = get_message_log(f"simulationLog_{NODE_TYPE}.txt", length=len(scenario) + 3)  # +3 for RECEIVE events
  
  

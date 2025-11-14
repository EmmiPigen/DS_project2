#!/usr/bin/env python3

# src/systemTest.py

"""
System Test for the Lamport and Vector Clock Implementations
----------------------------------------
Tests correctness of message ordering and overhead analysis
using the real network simulator and Node implementations.
"""


# autopep8: off
from email import message
from pdb import run
import time
from turtle import reset
import pytest
import json
import os
import sys
import struct
import binascii



sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.Lamport_timestamps.node import LamportNode as LamportNode
from src.Vector_clocks.node import VectorClockNode as VectorClockNode
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
  with open(log_file_path, 'r') as f:
    logs = [json.loads(line) for line in f.readlines()]
    for log in range(len(logs) - length, len(logs)):
      events.append({
          'node_id': logs[log]['node_id'],
          'event_type': logs[log]['event_type'],
          'clock': logs[log]['clock'],
          'details': logs[log]['details']
      })
  return events


def is_vector_less_than(vc1, vc2):
  """Checks if vector clock vc1 is less than vc2."""
  strictly_less = False
  for i in range(len(vc1)):
    if vc1[i] > vc2[i]:
      return False
    if vc1[i] < vc2[i]:
      strictly_less = True
  return strictly_less


def is_vector_comparable(vc1, vc2):
  """Checks if V1 < V2 or V2 < V1. ie., they are causally related."""
  return is_vector_less_than(vc1, vc2) or is_vector_less_than(vc2, vc1)

def reset_clocks(NODE_TYPE, manager):
    # Reset clocks
  for node in manager.nodes:
    if NODE_TYPE == "LAMPORT":
      node.lamport_Clock = 0
    if NODE_TYPE == "VECTOR":
      node.vector_Clock = [0 for _ in manager.nodes]
  with open(f"simulationLog_{NODE_TYPE}.txt", "a") as f:
    f.write("--- New Test Run ---\n")

# --- Fixtures ----------------------------------------------------------------

@pytest.fixture(params=["VECTOR", "LAMPORT"], scope="module")
def node_setup(request):
  NODE_TYPE = request.param
  NUM_NODES = 4

  manager = SimulationManager(NUM_NODES, NODE_TYPE)
  # Allow some time for nodes to start
  assert wait_until(lambda: len(manager.nodes) == NUM_NODES, timeout=15), "Nodes did not start in time"
  yield manager, NODE_TYPE
  # Teardown logic if needed
  for n in manager.nodes:
    n.is_alive = False
    time.sleep(1)  # Allow threads to exit
  del manager, NODE_TYPE


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

  # Reset clocks
  reset_clocks(NODE_TYPE, manager)

  # 1->2, 2->3, 3 LOCAL_EVENT, 3->4
  scenario = [
      (1, "SEND", 2),
      (2, "SEND", 3),
      (3, "LOCAL_EVENT", None),
      (3, "SEND", 4),
  ]

  run_scenario(manager, scenario, t=10)
  time.sleep(1)  # Ensure logs are flushed
  events = get_message_log(f"simulationLog_{NODE_TYPE}.txt", 7)  # 4 send/local + 3 receive

  events.reverse()  # Reverse to get chronological order
  for i in range(0, len(events)):
    if events[i]['event_type'] == "RECIEVE_MESSAGE":
      sender_id = int(events[i]['details'].split(" from Node ")[1])
      for j in range(i - 1, len(events)):
        if events[j]['node_id'] == sender_id and events[j]['event_type'] == "SEND_MESSAGE":
          if NODE_TYPE == "LAMPORT":
            assert events[j]['clock'] < events[i]['clock'], f"Message ordering violated between Node {sender_id} and Node {events[i]['node_id']}."
            break
          if NODE_TYPE == "VECTOR":
            assert is_vector_less_than(events[j]['clock'], events[i]['clock']), f"Message ordering violated between Node {sender_id} and Node {events[i]['node_id']}."


def test_message_complexity(node_setup):
  """
  Test message complexity to show that Vector Clocks have higher overhead but that they also satisfy O(1) and O(N) complexities for Lamport and Vector clocks respectively.
  """

  manager, NODE_TYPE = node_setup

  reset_clocks(NODE_TYPE, manager)

  scenario = [
      (1, "SEND", 2),
      (1, "SEND", 3),
      (1, "SEND", 4)
  ]

  run_scenario(manager, scenario, t=10)
  time.sleep(1)  # Ensure logs are flushed

  logs = get_message_log(f"simulationLog_{NODE_TYPE}.txt", 6)  # 3 sends + 3 receives

  message_sizes = []
  for entry in logs:
    if entry['event_type'] == "SEND_MESSAGE":
      clock = entry['clock']
      # Serialize clock to measure size
      if NODE_TYPE == "LAMPORT":
        packed = struct.pack('!I', clock)  # 4 bytes for Lamport clock
      else:  # VECTOR
        packed = b''.join(struct.pack('!I', vc) for vc in clock)  # 4 bytes per entry
      message_sizes.append(len(packed))

  avg_size = sum(message_sizes) / len(message_sizes)
  print(f"Average message size for {NODE_TYPE} clocks: {avg_size} bytes")

  if NODE_TYPE == "LAMPORT":  # Should be equal to 1 byte
    assert avg_size == 4, "Lamport clock message size too large, expected O(1) complexity."
  else:  # VECTOR # Should be proportional to number of nodes + comma
    N = len(manager.nodes)
    assert avg_size == N * 4, "Vector clock message size too small, expected O(N) complexity."


def test_space_complexity(node_setup):
  """
  Test space complexity to show that Vector Clocks have higher overhead to store the clocks than Lamport clocks.
  """
  manager, NODE_TYPE = node_setup

  space_usages = []
  for node in manager.nodes:
    if NODE_TYPE == "LAMPORT":
      space_usages.append(sys.getsizeof(node.lamport_Clock))
    else:  # VECTOR
      space_usages.append(sys.getsizeof(node.vector_Clock))

  avg_space = sum(space_usages) / len(space_usages)
  print(f"Average space usage for {NODE_TYPE} clocks: {avg_space} bytes")

  if NODE_TYPE == "LAMPORT":  # Should be equal to 1 byte
    assert avg_space == sys.getsizeof(0), "Lamport clock space usage too large, expected O(1) complexity."
  else:  # VECTOR # Should be proportional to number of nodes
    N = len(manager.nodes)
    expected_size = sys.getsizeof([0]*N)
    assert avg_space == expected_size, "Vector clock space usage too small, expected O(N) complexity."

#Only for vector clocks
@pytest.mark.parametrize("node_setup", ["VECTOR"], indirect=True)
def test_partial_ordering(node_setup):
  """
  Test that vector clocks can identify concurrent events.
  """    
  manager, NODE_TYPE = node_setup

  reset_clocks(NODE_TYPE, manager)

  n1, n2 = manager.nodes[0], manager.nodes[1]

  n1.local_event()  # N1: [1,0]
  n2.local_event()  # N2: [0,1]

  assert not is_vector_comparable(n1.vector_Clock, n2.vector_Clock), "Vector clocks should be concurrent but are comparable."
  


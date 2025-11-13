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

def get_node_by_id(nodes, node_id):
    """Helper to retrieve a node object by its ID."""
    return next((n for n in nodes if n.id == node_id), None)

def wait_until(condition_fn, timeout=10, poll=0.5):
  """Waits until condition_fn() returns True or timeout occurs."""
  start = time.time()
  while time.time() - start < timeout:
    if condition_fn():
      return True
    time.sleep(poll)
  return False

# --- Fixtures ----------------------------------------------------------------
@pytest.fixture(params=["VECTOR", "LAMPORT"], scope="module")
def node_setup(request):
    NODE_TYPE = request.param
    NUM_NODES = 4
    
    manager = SimulationManager(NUM_NODES, NODE_TYPE)
    # Allow some time for nodes to start
    assert wait_until(lambda: len(manager.nodes) == NUM_NODES, timeout=15), "Nodes did not start in time"
    yield manager.nodes, NODE_TYPE
    # Teardown logic if needed
    manager.stop_simulation()
        

# --- Tests --------------------------------------------------------------------

def test_startup(node_setup):
    nodes, NODE_TYPE = node_setup
    for node in nodes:
        assert node._status == "IDLE", f"Node {node.node_Id} did not start in IDLE state."
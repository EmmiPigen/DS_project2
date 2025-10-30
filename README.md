# DS_project2

This repository contains the code for a python implementation of the Lamport timestamp and vector clock algorithms. The code is located in the `src` folder, containing two folders, `lamportTimestamp` and `vectorClock`, each with their respective implementations. Inside each folder, there is a `node.py` file that contains the implementation of the node class, a file for the message object implementation for each algorithm. 

In the `src` folder, the files shared by both implementations include a `simulationManager.py` file to manage the simulation environment for the nodes, an abstract `LocalNode.py` class that defines the common functionality for both types of nodes, and a `evenetLogger.py` file to log the events, "local_event", "send_event", and "receive_event" to a .txt file logging the changes in timestamps or vector clocks. The `main.py` file is used to start the simulation by creating the simulation manager and initializing the nodes and allows for user input to trigger local events or message sending between nodes.


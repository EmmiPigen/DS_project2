# DS_project2

This repository contains the code for a python implementation of the Lamport timestamp and vector clock algorithms. The code is located in the `src` folder, containing two folders, `lamportTimestamp` and `vectorClock`, each with their respective implementations. Inside each folder, there is a `node.py` file that contains the implementation of the node class, a file for the message object implementation for each algorithm. 

In the `src` folder, the files shared by both implementations include a `simulationManager.py` file to manage the simulation environment for the nodes, an abstract `LocalNode.py` class that defines the common functionality for both types of nodes, and a `evenetLogger.py` file to log the events, "local_event", "send_event", and "receive_event" to a .txt file logging the changes in timestamps or vector clocks. The `main.py` file is used to start the simulation by creating the simulation manager and initializing the nodes and allows for user input to trigger local events or message sending between nodes.


## How to run the implementation

To run the implementation, navigate to the `src` folder in your terminal and run the `simulationManager.py` file using the command:

```bash
python simulationManager.py <numberOfKnownNodes> [<NODE_TYPE>] 
```

Where `<numberOfKnownNodes>` are the number of nodes you want to create in the network. 
`<NODE_TYPE>` is an optional argument to specify which type of node to use, either "LAMPORT" or "VECTOR". If not specified, it defaults to "LAMPORT".

For example, to create 4 nodes, you would run:

```bash
python simulationManager.py 4 LAMPORT
```

This will start the simulation manager and create the specified number of Lamport nodes. The simulation manager starts a network simulator too, that handles message passing between the nodes.

After starting the simulation manager, you can control each node in the same terminal using the implemented commands: "status" and "contact".

- `status <node_id>`: Prints the current status of the specified node, including its known nodes and current timestamp or vector clock.
- `contact <node_id> <target_id>`: Sends a message from the specified node to the target node, updating the timestamp or vector clock accordingly.


## Tests
A system test file `systemTest.py` is used to test the implementation of both Lamport timestamps and vector clocks and testing for the correctness of the ordering of events and the overhead analysis. To run the tests, navigate to the `src` folder in your terminal and run the following command:

```bash
pytest -v .\systemTest.py
```

## Note 
The implementation is a simulation and does not handle all edge cases or failures that may occur in a real distributed system. It is intended for educational purposes to demonstrate the Bully Election Algorithm and its improved version.

The implementation assumes that all nodes are started manually and that the network simulator is running before starting any nodes, initial election are not automatically started when nodes are started, and should be initiated manually by entering the `election` command in the node terminal.

When node recovers (revive command), it does automatically start an election, as per the Bully algorithm specification.

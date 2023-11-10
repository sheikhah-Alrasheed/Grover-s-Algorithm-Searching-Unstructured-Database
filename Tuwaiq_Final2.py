import numpy as np
import time
from qiskit import QuantumCircuit, transpile, Aer, IBMQ
from qiskit.visualization import *
from qiskit.providers.aer import QasmSimulator
from qiskit.circuit.library.standard_gates import XGate
from operator import *
from qiskit.visualization import plot_histogram

item = input('Enter name of an item:')

# Define the quantum search parameters
n = 4
N = (2**n)

index_colour_table = {}
colour_hash_map = {}

if n == 3:
    
    index_colour_table = {'000': "yellow", '001': "red", '010': "blue", '011': "red", '100': "green", '101': "blue",'110': "orange", '111': "red"}
    colour_hash_map = {"yellow": '100', "red": '011', "blue": '000', "green": '001', "orange": '010'}

elif n == 4:
    index_colour_table = {'0000': "red", '0001': "orange", '0010': "blue", '0011': "green", '0100': "yellow",
                          '0101': "purple", '0110': "pink", '0111': "brown", '1000': "cyan", '1001': "magenta",
                          '1010': "gray", '1011': "black", '1100': "white", '1101': "violet", '1110': "indigo",
                          '1111': "turquoise"}
    
    colour_hash_map = {"red": '0000', "orange": '0001', "blue": '0010', "green": '0011', "yellow": '0100', "purple": '0101',
        "pink": '0110', "brown": '0111', "cyan": '1000', "magenta": '1001', "gray": '1010', "black": '1011',
        "white": '1100', "violet": '1101', "indigo": '1110', "turquoise": '1111'} 

def database_oracle(index_colour_table, colour_hash_map):
    circ_database = QuantumCircuit(n + n)
    for i in range(N):
        circ_data = QuantumCircuit(n)
        idx = bin(i)[2:].zfill(n)
        colour = index_colour_table[idx]
        colour_hash = colour_hash_map[colour][::-1]
        for j in range(n):
            if colour_hash[j] == '1':
                circ_data.x(j)
        data_gate = circ_data.to_gate(label=colour).control(num_ctrl_qubits=n, ctrl_state=idx, label="index-" + colour)
        circ_database.append(data_gate, list(range(n + n)))
    return circ_database

database_oracle(index_colour_table, colour_hash_map).draw()
circ_data = QuantumCircuit(n)

m = 0
if n == 2:
    m = 3
elif n == 3:
    m = 4
idx = bin(m)[2:].zfill(n) 
colour = index_colour_table[idx]
colour_hash = colour_hash_map[colour][::-1]
for j in range(n):
    if colour_hash[j] == '1':
        circ_data.x(j)
               
circ_data.draw()

def oracle_grover(database, data_entry):
    circ_grover = QuantumCircuit(n + n + 1)
    circ_grover.append(database, list(range(n + n)))
    target_reflection_gate = XGate().control(num_ctrl_qubits=n, ctrl_state=colour_hash_map[data_entry],
                                             label="Reflection of " + "\"" + data_entry + "\" Target")
    circ_grover.append(target_reflection_gate, list(range(n, n + n + 1)))
    circ_grover.append(database, list(range(n + n)))
    return circ_grover

oracle_grover(database_oracle(index_colour_table, colour_hash_map).to_gate(label="Database Encoding"), item).decompose().draw()

def mcz_gate(num_qubits):
    num_controls = num_qubits - 1
    mcz_gate = QuantumCircuit(num_qubits)
    target_mcz = QuantumCircuit(1)
    target_mcz.z(0)
    target_mcz = target_mcz.to_gate(label="Z_Gate").control(num_ctrl_qubits=num_controls, ctrl_state=None, label="MCZ")
    mcz_gate.append(target_mcz, list(range(num_qubits)))
    return mcz_gate.reverse_bits()

mcz_gate(n).decompose().draw()

def diffusion_operator(num_qubits):
    circ_diffusion = QuantumCircuit(num_qubits)
    qubits_list = list(range(num_qubits))
    circ_diffusion.h(qubits_list)
    circ_diffusion.x(qubits_list)
    circ_diffusion = circ_diffusion.compose(mcz_gate(num_qubits), qubits_list)
    circ_diffusion.x(qubits_list)
    circ_diffusion.h(qubits_list)
    return circ_diffusion

diffusion_operator(n).draw()

circuit = QuantumCircuit(n + n + 1, n)
circuit.x(n + n)
circuit.barrier()
circuit.h(list(range(n)))
circuit.h(n + n)
circuit.barrier()
unitary_oracle = oracle_grover(database_oracle(index_colour_table, colour_hash_map).to_gate(label="Database Encoding"), item).to_gate(label="Oracle Operator")
unitary_diffuser = diffusion_operator(n).to_gate(label="Diffusion Operator")

M = countOf(index_colour_table.values(), item)
Q = int(np.pi * np.sqrt(N / M) / 4)

for i in range(Q):
    circuit.append(unitary_oracle, list(range(n + n + 1)))
    circuit.append(unitary_diffuser, list(range(n)))
circuit.barrier()
circuit.measure(list(range(n)), list(range(n)))

start_time = time.time()
backend_sim = Aer.get_backend('qasm_simulator')
job_sim = backend_sim.run(transpile(circuit, backend_sim), shots=1024)
result_sim = job_sim.result()
counts = result_sim.get_counts(circuit)

end_time = time.time()

elapsed_time_ms = (end_time - start_time) * 1000

if M==1:
    print("Index of the colour", item, "is the index with most probable outcome")
else:
    print("Indices of the colour", item, "are the indices the most probable outcomes")

plot_histogram(counts)

print(f"The total running time of searching : {elapsed_time_ms} ms")

import quantx
from quantx import search 

quantx.set_backend("ibm_kingston", token="S1sBe0IbcQ8xqPox3i2x2xVMpMqdcw06IeWTrEWlYc5C")



result = search(["alice", "bob", "charlie", "diana"], target="charlie")
print(result.found)       # True
print(result.confidence)  # 1.0 (100%)

# Search through numbers
result = search(list(range(16)), target=7)
print(result.found)       # True
print(result.confidence)  # ~0.96
print(result.iterations)  # 3 (optimal Grover iterations)
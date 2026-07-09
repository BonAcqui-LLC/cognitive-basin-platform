import sys
sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\02_REFERENCE_IMPLEMENTATION")
sys.path.insert(0, r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\03_EXPERIMENTS")
import natural_math_v5 as nm
from natural_math_v5.records import make_node
from natural_math_v5.randomness import TraceRng
from extension_harness import Mode, NoopExtension, run_local

params = nm.default_params()
noop = NoopExtension()
nodes = [make_node(1,(0,0,0),energy=1000000,node_type="seed"),
         make_node(2,(2,0,0),energy=1000000,node_type="tip")]

out = run_local(nodes, params, mode=Mode.HARNESS_WITH_EXTENSIONS,
               extensions=[noop], rng=TraceRng(42))
print("Hook counts:", noop.hook_counts)
print("Hook events:", len(out["hook_events"]))
for ev in out["hook_events"]:
    print("  %s: %s" % (ev["hook"], ev["result_type"]))

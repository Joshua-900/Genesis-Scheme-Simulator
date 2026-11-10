import concurrent.futures
import json
from pathlib import Path
import sys
from src.genesis_v3.wall_handoff import run, prepare

def branch(size, damping, prepared):
    result = run(size, 405, duration=.3, padding=(size-1)//8, travel_gate=True,
                 prepared=prepared, partition_overlap=True, damping=damping)
    result['damping'] = damping
    path = Path('results/genesis_v3_fixed_rule') / f'known_pair_{size}_damping_{damping:g}.json'
    path.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    last = result['records'][-1]
    print(size, damping, result['outcome'], last['time'], last.get('travel_diameters'),
          last.get('separation_change'), [core['charge'] for core in last['cores']], flush=True)

if __name__ == '__main__':
    from concurrent.futures import ThreadPoolExecutor
    size = int(sys.argv[1])
    prepared = prepare(size, 405, mature=True)
    with ThreadPoolExecutor(2) as pool:
        tasks = [pool.submit(branch, size, d, prepared) for d in (0., .75)]
        for task in concurrent.futures.as_completed(tasks):
            task.result()

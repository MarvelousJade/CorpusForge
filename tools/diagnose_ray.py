"""Read local Ray session logs when a small fixture stalls."""
from pathlib import Path
import tempfile

roots = [Path(tempfile.gettempdir())/'ray']
for root in roots:
    sessions = sorted(root.glob('session_*'), key=lambda p: p.stat().st_mtime)
    if not sessions:
        print('No Ray sessions under', root)
        continue
    session = sessions[-1]
    print('Latest session:', session)
    for name in ('gcs_server.out','gcs_server.err','raylet.out','raylet.err','dashboard.log','monitor.log'):
        path = session/'logs'/name
        if path.exists():
            print('\n---', name, '---\n', path.read_text(errors='replace')[-7000:])

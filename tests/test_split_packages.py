import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

spec = importlib.util.spec_from_file_location('packages', Path(__file__).resolve().parents[1]/'tools/build_packages.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_split_packages_are_standalone_and_clean(tmp_path):
    output = module.build(tmp_path/'distribution')
    for name in ('server', 'agent'):
        folder = output/name
        manifest = json.loads((folder/'MANIFEST.json').read_text())
        for relative, expected in manifest['files'].items():
            path = folder/relative
            assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
            assert path.suffix not in {'.db', '.pyc', '.log', '.pem', '.key'}
            assert path.name != '.env'
            if path.suffix == '.py':
                compile(path.read_bytes(), str(path), 'exec')
        with zipfile.ZipFile(output/(name+'.zip')) as archive:
            assert archive.testzip() is None
            assert set(archive.namelist()) == {name+'/'+p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
    env = {**os.environ, 'EDR_ENV': 'test', 'EDR_JWT_SECRET': 'package-test-'+'z'*64,
           'EDR_DATA_DIR': str(tmp_path/'server-data'), 'EDR_BACKGROUND': 'false',
           'EDR_AGENT_DATA': str(tmp_path/'agent-data'), 'EDR_API_KEY': 'test-only-'+'a'*40}
    for name, code in [('server', "import sys; sys.path.insert(0,'backend'); from server import create_app; assert create_app().test_client().get('/ready').status_code==200"),
                       ('agent', "import sys; sys.path.insert(0,'endpoint'); import agent,sysmon_collector; assert agent.SYSTEM_ID")]:
        result = subprocess.run([sys.executable, '-c', code], cwd=output/name, env=env,
                                capture_output=True, text=True, timeout=45)
        assert result.returncode == 0, result.stderr
    with pytest.raises(FileExistsError):
        module.build(output)

"""Read-only repository inventory; source declarations are not live bindings."""
import ast
import json
from pathlib import Path
import subprocess
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def collect():
    rows = []
    names = {'HOSTNAME', 'WORKER', 'BRANCH', 'SOURCE_ROOT'}
    for path in sorted((ROOT / 'scripts').glob('*/publish.py')):
        values = {}
        for node in ast.parse(path.read_text(encoding='utf-8')).body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in names:
                        values[target.id] = node.value.value
        if len(values) == 4 and all(isinstance(value, str) and value for value in values.values()):
            rows.append(dict(hostname=values['HOSTNAME'], worker=values['WORKER'],
                             branch=values['BRANCH'], root=values['SOURCE_ROOT'],
                             evidence=path.relative_to(ROOT).as_posix()))
    registry = json.loads((ROOT / '.github/site-factory-sites.json').read_text(encoding='utf-8'))
    for site in registry['sites'].values():
        hostname = urlsplit(site['siteUrl']).hostname
        if hostname in {'blog.fwith.kr', 'fwith.kr'}:
            continue
        deployment = site.get('coverageDeployment', {})
        rows.append(dict(hostname=hostname, worker=deployment.get('worker', site['worker']),
                         branch=site['branch'], root=site['root'],
                         evidence='.github/site-factory-sites.json',
                         registryWorker=site['worker']))
    for row in rows:
        assert row['hostname'].endswith('.fwith.kr')
        assert row['worker'] != 'generic-skycar-shadow'
        try:
            row['sourceBranchHead'] = git('rev-parse', '--verify', 'refs/remotes/origin/' + row['branch'])
        except subprocess.CalledProcessError:
            row['sourceBranchHead'] = None
        row.update(liveBindingVerified=False, activeVersionUUID=None, deployedSourceSHA=None,
                   deployedFileInventory=None)
    return dict(controlSHA=git('rev-parse', 'HEAD'),
                status='repository_declarations_only_not_deployment_inventory',
                uniqueHostnames=len({row['hostname'] for row in rows}), declarations=rows)


if __name__ == '__main__':
    print(json.dumps(collect(), ensure_ascii=False, indent=2))

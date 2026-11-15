#!/usr/bin/env python3
"""Prepare a bounded, test-only Odoo invocation plan; never starts a process.

The caller must apply BOTH returned read-only mounts and pass odoo_args to the
isolated Odoo test process. This is not a UAT lifecycle or ledger controller.
"""
import argparse
import ast
import json
import os
from pathlib import Path
import re
import shutil
import sys

SELECTORS = {'amr_resource', 'amr_oidc', 'amr_oidc_resource'}
FORBIDDEN = {'amr_oidc', 'amr_token', 'amr_oidc_resource'}
NAME = re.compile(r'^[a-zA-Z0-9_]+$')


def checked_root(value):
    path = Path(value).absolute()
    for part in (path,) + tuple(path.parents):
        if part.is_symlink():
            raise ValueError('symlink in root path')
    if not path.is_dir():
        raise ValueError('root must be a directory')
    # Check the original components before collapsing '..', so a symlink
    # hidden by traversal is still rejected. This is not race-safe (TOCTOU).
    return Path(os.path.abspath(str(path)))


def reject_links(root):
    for parent, dirs, files in os.walk(str(root), followlinks=False):
        for item in dirs + files:
            if (Path(parent) / item).is_symlink():
                raise ValueError('symlinks are not allowed')


def dependencies(path):
    manifest = ast.literal_eval((path / '__manifest__.py').read_text(encoding='utf-8'))
    deps = manifest.get('depends', [])
    if not isinstance(deps, (list, tuple)) or any(not isinstance(x, str) or not NAME.fullmatch(x) for x in deps):
        raise ValueError('invalid dependency name')
    return deps


def prepare(source, core, output, selector):
    if selector not in SELECTORS:
        raise ValueError('unsupported selector')
    source, core = checked_root(source), checked_root(core)
    output = Path(output).absolute()
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise ValueError('output must be a new directory')
    output = checked_root(output.parent) / output.name
    if any(p == output or p in output.parents or output in p.parents for p in (source, core)):
        raise ValueError('source, core and output must be disjoint')
    if ',' in str(output) or ',' in str(core):
        raise ValueError('comma is invalid in mount path')
    reject_links(source)
    reject_links(core)
    if selector == 'amr_resource':
        if any((core / name).exists() for name in FORBIDDEN):
            raise ValueError('forbidden sibling present in core addon path')
        selected, visited, active = set(), set(), set()

        def visit(name):
            if name in FORBIDDEN:
                raise ValueError('forbidden first-party dependency: ' + name)
            if name in active:
                raise ValueError('dependency cycle: ' + name)
            if name in visited:
                return
            addon = source / name
            if addon.is_dir():
                selected.add(name)
            else:
                addon = core / name
            if not (addon / '__manifest__.py').is_file():
                raise ValueError('missing dependency: ' + name)
            active.add(name)
            for dep in dependencies(addon):
                visit(dep)
            active.remove(name)
            visited.add(name)

        visit(selector)
        output.mkdir()
        try:
            for name in sorted(selected):
                shutil.copytree(str(source / name), str(output / name))
        except Exception:
            shutil.rmtree(str(output))
            raise
    else:
        raise ValueError('full snapshot copy requires a verified snapshot contract; unavailable')
    mount = 'type=bind,src=' + str(output) + ',dst=/mnt/extra-addons,readonly'
    core_mount = 'type=bind,src=' + str(core) + ',dst=/odoo-core,readonly'
    addons_path = ['/mnt/extra-addons', '/odoo-core']
    return {'mount': mount, 'core_mount': core_mount, 'addons_path': addons_path,
            'odoo_args': ['--addons-path=' + ','.join(addons_path)] +
                         (['--proxy-mode'] if selector == 'amr_oidc' else [])}


def main():
    parser = argparse.ArgumentParser()
    for arg in ('source', 'core', 'output', 'selector'):
        parser.add_argument('--' + arg, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.source, args.core, args.output, args.selector)))
    except (ValueError, OSError, SyntaxError) as error:
        print('prepare_run: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

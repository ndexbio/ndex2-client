#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Verifies a built wheel contains every package present in the source tree.

``setup.py`` lists packages explicitly rather than by wildcard, so adding a
new subdirectory with an ``__init__.py`` requires updating that list. Forget
to, and the directory is silently dropped from the wheel: the source tree
still works, the test suite still passes, and the published package fails to
import.

Nothing else in CI catches this, because ``pytest`` runs from the repository
root and therefore imports the local source rather than the installed
package.

Usage::

    python scripts/check_packaging.py dist/ndex2-3.12.0-py2.py3-none-any.whl

Exits non-zero, listing the missing packages, if any are absent.
"""

import glob
import os
import sys
import zipfile

# Directories that are deliberately not shipped.
EXCLUDED = ('tests',)

# Top level packages expected in the wheel.
ROOTS = ('ndex2', 'ndex2cx')


def source_packages(root='.'):
    """
    Finds every importable package directory in the source tree.

    :param root: Directory to search from
    :type root: str
    :return: Package directories, as paths relative to *root*
    :rtype: set
    """
    found = set()
    for top in ROOTS:
        top_path = os.path.join(root, top)
        if not os.path.isdir(top_path):
            continue
        for dirpath, dirnames, filenames in os.walk(top_path):
            dirnames[:] = [d for d in dirnames
                           if d not in EXCLUDED and
                           not d.startswith('.') and
                           d != '__pycache__']
            if '__init__.py' not in filenames:
                continue
            rel = os.path.relpath(dirpath, root).replace(os.sep, '/')
            if any(part in EXCLUDED for part in rel.split('/')):
                continue
            found.add(rel)
    return found


def wheel_packages(wheel_path):
    """
    Finds every package directory represented inside a wheel.

    :param wheel_path: Path to the ``.whl`` file
    :type wheel_path: str
    :return: Package directories found in the archive
    :rtype: set
    """
    found = set()
    with zipfile.ZipFile(wheel_path) as archive:
        for name in archive.namelist():
            if not name.endswith('/__init__.py'):
                continue
            pkg = name[:-len('/__init__.py')]
            if pkg.split('/')[0] in ROOTS:
                found.add(pkg)
    return found


def main():
    if len(sys.argv) < 2:
        sys.stderr.write('usage: check_packaging.py <wheel or glob>\n')
        return 2

    matches = []
    for arg in sys.argv[1:]:
        matches.extend(sorted(glob.glob(arg)))
    wheels = [m for m in matches if m.endswith('.whl')]
    if not wheels:
        sys.stderr.write('ERROR: no wheel matched %s\n'
                         % ' '.join(sys.argv[1:]))
        return 2
    if len(wheels) > 1:
        sys.stderr.write('ERROR: expected one wheel, found %d: %s\n'
                         % (len(wheels), ', '.join(wheels)))
        return 2

    wheel = wheels[0]
    expected = source_packages()
    actual = wheel_packages(wheel)
    missing = sorted(expected - actual)

    print('wheel:    %s' % wheel)
    print('expected: %s' % ', '.join(sorted(expected)))
    print('in wheel: %s' % ', '.join(sorted(actual)))

    if missing:
        sys.stderr.write(
            '\nERROR: these packages exist in the source tree but are '
            'missing from the wheel:\n')
        for pkg in missing:
            sys.stderr.write('  %s\n' % pkg)
        sys.stderr.write(
            "\nAdd them to the packages= list in setup.py. Note that a "
            "module\ninside an already listed package ships automatically, "
            "but a\nsubdirectory with its own __init__.py does not.\n")
        return 1

    print('\nOK: every source package is present in the wheel.')
    return 0


if __name__ == '__main__':
    sys.exit(main())

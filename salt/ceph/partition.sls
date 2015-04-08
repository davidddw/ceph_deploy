
include:
  - .repo

parted:
  pkg.installed:
    - name: parted
    - fromrepo: ceph
    - require:
      - pkgrepo: pkg_repo

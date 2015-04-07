include:
  - .repo

ceph_pkg:
  pkg.installed:
    - name: ceph
    - fromrepo: ceph
    - require: 
      - pkgrepo: pkg_repo
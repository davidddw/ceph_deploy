include:
  - .repo

ceph_pkg:
  pkg.latest: 
    - name: ceph
    - fromrepo: ceph
    - require: 
      - pkgrepo: pkg_repo
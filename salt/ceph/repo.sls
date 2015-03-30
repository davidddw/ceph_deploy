{% set repoip = salt['pillar.get']('nodes:master:ip') -%}

ceph_repo:
  pkgrepo.managed:
    - humanname: ceph
    - name: ceph
    - baseurl: http://{{ repoip }}/
    - gpgcheck: 0
    - enabled: 1

{% set repoip = salt['pillar.get']('nodes:master:ip') -%}

pkg_repo:
  pkgrepo.managed:
    - humanname: ceph0
    - name: ceph
    - baseurl: http://{{ repoip }}/
    - gpgcheck: 0
    - enabled: 1

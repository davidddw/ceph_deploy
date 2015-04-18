pkg_repo:
  pkgrepo.managed:
    - humanname: ceph
    - name: ceph
    - baseurl: http://{{ salt['pillar.get']('nodes:master:ip') }}/
    - gpgcheck: 0
    - enabled: 1

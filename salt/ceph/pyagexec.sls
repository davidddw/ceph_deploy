
py_conf_setup: 
  file.managed:
    - name: /usr/local/livecloud/pyagexec/pyagexec.cfg 
    - source: salt://ceph/files/pyagexec.cfg
    - template: jinja
    - require_in:
      - service: py_service
      
py_service: 
  service.running: 
    - name: pyagexec
    - enable: True
    - watch: 
      - file: py_conf_setup

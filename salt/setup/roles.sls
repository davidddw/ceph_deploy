salt-minion:
  pkg.installed: []
  service.running:
    - watch:
      - file: /etc/salt/grains
    - require:
      - pkg: salt-minion

/etc/salt/grains:
  file.managed:
    - template: jinja
    - source: salt://salt/etc/grains
    - require:
      - pkg: salt-minion
    - require_in:
      - service: salt-minion
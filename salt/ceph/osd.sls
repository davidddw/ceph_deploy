{% import 'ceph/global_vars.jinja' as conf with context -%}

include:
  - .ceph

{% for dev in salt['pillar.get']('nodes:' + conf.host + ':devs') -%}
{% if dev -%}
{% set journal = salt['pillar.get']('nodes:' + conf.host + ':devs:' + dev + ':journal') -%}
{% set uuid = salt['cmd.run']('uuidgen') -%}
{% set osd_id = salt['cmd.run']('ceph osd create ' ~ uuid) -%}

ceph_osd_{{ osd_id }}:
  ceph_deploy:
    - create_osd
    - osd_id: {{ osd_id }}
    - dev: {{ dev }}
    - uuid: {{ uuid }}
    - journal_dev: {{ journal }}
    - curr_host: {{ conf.host }} 

ceph_conf_update_{{ osd_id }}:
  ini.sections_present:
    - name: /etc/ceph/{{ conf.cluster }}.conf
    - sections:
        osd.{{ osd_id }}:
          host: {{ conf.host }}

{% endif -%}
{% endfor -%}

setup_autostart:
  cmd.run: 
    - name: echo "/etc/init.d/ceph start" >> /etc/rc.local

start ceph-osd-all:
  cmd.run: 
    - name: /etc/init.d/ceph start osd
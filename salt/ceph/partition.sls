{% import 'ceph/global_vars.jinja' as conf with context -%}

include:
  - .repo

parted:
  pkg.installed:
    - name: parted
    - fromrepo: ceph
    - require:
      - pkgrepo: ceph_repo

{% for journal in salt['pillar.get']('nodes:' + conf.host + ':journal') -%}
{% if journal -%}
{% set partition = salt['pillar.get']('nodes:' + conf.host + ':journal:' + journal + ':partition') -%}

partition_table:
  cmd.run:
    - name: |
        parted -s /dev/{{ journal }} \
            {% for parti in partition -%}
            mkpart primary xfs {{ parti['from'] }} {{ parti['to'] }} \
            {% endfor -%}
    - unless: parted -s /dev/{{ journal }} print | grep primary

{% endif -%}
{% endfor -%}
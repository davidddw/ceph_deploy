{% set host = salt['config.get']('host') -%}

include:
  - .repo

parted:
  pkg.installed:
    - name: parted
    - fromrepo: ceph
    - require:
      - pkgrepo: pkg_repo

{% for journal in salt['pillar.get']('nodes:' + host + ':journal') -%}
{% if journal -%}
{% set partition = salt['pillar.get']('nodes:' + host + ':journal:' + journal + ':partition') -%}

parted_mklabel:
  cmd.run:
    - name: parted -s /dev/{{ journal }} mklabel gpt

parted_mktable:
  cmd.run:
    - name: |
        parted -s /dev/{{ journal }} \
            {% for parti in partition -%}
            mkpart primary xfs {{ parti['from'] }} {{ parti['to'] }} \
            {% endfor %}

    - unless: parted -s /dev/{{ journal }} print | grep primary
    - require:
      - cmd: parted_mklabel 

{% endif -%}
{% endfor -%}
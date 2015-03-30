{%- set fqdn = grains['id'] %}

{%- set addrs = salt['mine.get']('*', 'network.ip_addrs') %}

{%- if addrs is defined %}

{%- for name, addrlist in addrs.items() %}
{{ name }}-host-entry:
  host.present:
    - ip: {{ addrlist|first() }}
    - names:
      - {{ name }}
{% endfor %}

{% endif %}
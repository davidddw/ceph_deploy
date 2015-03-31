rm -fr /var/cache/salt/master
systemctl restart salt-master

cat <<EOF > /etc/salt/roster 
centos151:
  host: 172.16.39.151
  user: root
  passwd: yunshan3302
centos152:
  host: 172.16.39.152
  user: root
  passwd: yunshan3302
centos153:
  host: 172.16.39.153
  user: root
  passwd: yunshan3302
EOF

salt-ssh '*' -r 'echo "172.16.39.11 centos39_11" >> /etc/hosts'

salt-ssh '*' state.sls setup.minion -l all -v   

salt '*' saltutil.sync_states

salt '*' state.highstate -l all -v  

salt '*' state.sls ceph.mon -l all -v

salt '*' state.sls ceph.osd -l all -v
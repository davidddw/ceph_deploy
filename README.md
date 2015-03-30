rm -fr /var/cache/salt/master
systemctl restart salt-master

salt-ssh '*' -r 'echo "172.16.39.11 centos39_11" >> /etc/hosts'

salt-ssh '*' state.sls setup.minion -l all -v   

salt '*' saltutil.sync_states

salt '*' state.highstate -l all -v  

salt '*' state.sls ceph.partition

salt '*' state.sls ceph.mon -l all -v

salt '*' state.sls ceph.osd -l all -v
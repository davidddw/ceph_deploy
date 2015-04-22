vim master.yml
vim ceph.yml

python setup.py
salt-ssh '*' -r 'echo "172.16.39.150 centos150" >> /etc/hosts'
salt-ssh '*' state.sls ceph.minion

salt-key -L
salt-key -A -y
salt '*' state.highstate
salt '*' state.sls ceph.ntp
salt '*' state.sls ceph.ceph
salt '*' state.sls ceph.kvm

python caller.py
#salt '*' saltutil.sync_all
#salt '*' ceph.journal
#salt '*' ceph.mon
#salt '*' ceph.osd
#salt '*' ceph.pool

#salt '*' kvm.pool

#salt '*' state.sls ceph.pyagexec

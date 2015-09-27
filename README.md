#############################################
# read me first
#
# 部署之前请执行sh install.sh来配置salt-master
# 如果之前已经安装过salt-minion，请执行
# rm -fr /var/cache/salt/minion/* && systemctl restart salt-minion
# 或者执行
# salt '*' saltutil.clear_cache
#
# 之后编辑如下两个文件
vim master.yml
vim ceph.yml

# 如果没有单独的journal 盘，每个节点上的配置如下
#   centos154: 
#   roles: 
#   - ceph-osd
#   - ceph-mon
#   devs: 
#   - vdc 
#   - vdd  

# 确认无误后，执行
python setup.py

# 安装salt-minion，并配置roser
salt-ssh '*' -r 'echo "172.16.39.150 centos150" >> /etc/hosts'
salt-ssh '*' state.sls ceph.minion

# 认证key
salt-key -L
salt-key -A -y

# 状态同步
salt '*' state.highstate        # 状态同步
salt '*' state.sls ceph.ntp         # 安装并配置ntp
salt '*' state.sls ceph.ceph        # 安装ceph
salt '*' state.sls ceph.kvm         # 安装kvm

# 分别执行如下命令
# python caller.py

salt '*' saltutil.refresh_pillar    # 更新pillar
salt '*' saltutil.sync_all      # 更新模块
salt '*' ceph.journal           # 配置journal盘
salt '*' ceph.mon           # 配置mon
salt '*' ceph.osd           # 配置osd
salt '*' ceph.pool          # 配置pool
salt '*' kvm.pool           # 配置kvm-pool
salt '*' state.sls ceph.pyagexec    # 配置pyagexec

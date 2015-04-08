include:
  - .repo

kvm_pkg:
  pkg.installed:
    - name: kvm 
    - pkgs: [qemu, seabios-bin, dejavu-lgc-sans-fonts, seabios, ipxe-roms-qemu,
             vim-enhanced, lvm2]
    - fromrepo: ceph
    - allow_updates: True
    - refresh: True
    - require: 
      - pkgrepo: pkg_repo

libvirt_pkg:
  pkg.installed:
    - name: libvirt 
    - pkgs: [libvirt, libvirt-daemon-kvm, virt-install, virt-manager, virt-top,
             virt-who, virt-viewer, libvirt-python]
    - fromrepo: ceph
    - allow_updates: True
    - refresh: True
    - require: 
      - pkg: kvm_pkg
      - pkgrepo: pkg_repo
      
libvirt_service: 
  service.running: 
    - name: libvirtd
    - enable: True
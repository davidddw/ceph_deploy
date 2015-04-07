include:
  - .repo

kvm_pkg:
  pkg.installed:
    - name: |
        qemu libvirt libvirt-daemon-kvm virt-install virt-manager virt-top \
          virt-who virt-viewer seabios-bin dejavu-lgc-sans-fonts seabios \
          ipxe-roms-qemu libvirt-python
    - fromrepo: ceph
    - require: 
      - pkgrepo: pkg_repo
      
libvirt_service: 
  service.running: 
    - name: libvirtd
    - enable: True
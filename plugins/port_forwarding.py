# -*- coding: utf-8 -*-
import sys
from subprocess import PIPE, Popen
from utils.logger import STREAM

class Keyword:
    """
    This plugin allows to forwarding ports beetwen guest and host machines.
    Arguments of actions.ini:
    vm_name = name of the virtual machine in VboxManage (example: vm_name = ubuntu1610-amd64_1523264320143_80330)
    forwarding_ports = name:guest:host, ... (example: forwarding_ports = vm_ssh:22:2020, icap:1344:1234)
    """

    def main(self):
        # - Use Config attributes
        self.vm_name = self.vm_name
        # self.forwarding_ports input format: name:guest:host, ... ex: vm_ssh:22:2020, icap:1344:1234
        self.forwarding_ports = self.forwarding_ports
        #----------------------------------
        self.forward()

    def check_vm_status(self):
        STREAM.info("==> Check Vm status.")
        rvms = Popen("VBoxManage list runningvms | awk '{print $1}'", shell=True, stdout=PIPE, stderr=PIPE)
        data = rvms.stdout.read()
        if self.vm_name in data:
            STREAM.info(" -> VM is ON")
            return True
        STREAM.info(" -> VM is turned off")
        return False

    def forward(self):
        if self.check_vm_status():
            STREAM.error(" -> Unable to forwarding ports, machine is booted.")
            return
        self.forwarding_ports = [ports.strip() for ports in self.forwarding_ports.split(",")]
        for item in self.forwarding_ports:
            name, guest, host = item.split(":")
            STREAM.debug("%s, %s, %s" % (name, guest, host))
            STREAM.info("==> Forwarding ports %s(guest) => %s(host)" % (guest, host))
            Popen("vboxmanage modifyvm %s --natpf1 delete %s" % (self.vm_name, name), shell=True, stdout=sys.stdout, stderr=sys.stdout).communicate()
            Popen("vboxmanage modifyvm %s --natpf1 %s,tcp,127.0.0.1,%s,,%s" % (self.vm_name, name, host, guest), shell=True, stdout=sys.stdout, stderr=sys.stdout).communicate()


if __name__ == "__main__":
    pass

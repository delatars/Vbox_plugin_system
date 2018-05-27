# -*- coding: utf-8 -*-
import os
import hashlib
import sys
import shutil
import tarfile
from datetime import datetime
from subprocess import Popen
from utils.logger import STREAM
from utils.auxilary import timer


class Keyword:
    """
    This plugin allows to export your virtual machine, to vagrant catalog.
    Arguments of actions.ini:
    vm_name = name of the virtual machine in VboxManage (example: vm_name = ubuntu1610-amd64_1523264320143_80330)
    self.vagrant_catalog = path to vagrant catalog (example: self.vagrant_catalog = /var/www/vagrant)
    """

    def main(self):
        # - Config attributes
        self.vm_name = self.vm_name
        self.vagrant_catalog = self.vagrant_catalog
        # ----------------------------
        self.vagrant_server_box_location_url = "http:\/\/vagrant.i.drweb.ru\/files\/unix"
        self.provider = "virtualbox"
        self.version = datetime.now().strftime("%Y%m%d%H%M")
        self.boxname = "%s_%s_%s.box.prep" % (self.vm_name, self.version, self.provider)
        result = self.export_vm_configuration()
        if result:
            self.create_vagrant_template()
            self.create_box()
            self.create_metadata_file()
            self.renew_vm()
            STREAM.success("==> Exporting into vagrant successfully completed.")

    def _calculate_box_hash(self):
        with open(os.path.join(self.work_dir, self.boxname), 'rb') as f:
            contents = f.read()
            hash = hashlib.sha1(contents).hexdigest()
            return hash

    @timer
    def create_box(self):
        STREAM.info("==> Creating box...")
        with tarfile.open(os.path.join(self.work_dir, self.boxname), "w") as tar:
            for fil in os.listdir(self.tmp_dir):
                tar.add(os.path.join(self.tmp_dir, fil), arcname=fil)
        STREAM.info(" -> Clearing temporary files")
        shutil.rmtree(self.tmp_dir)

    def create_metadata_file(self):
        STREAM.info("==> Calculating box checksum...")
        checksum = self._calculate_box_hash()
        STREAM.debug(" -> sha1 checksum: %s" % checksum)
        STREAM.info("==> Creating metadata.json")
        url = "\/".join([self.vagrant_server_box_location_url, self.vm_name, self.boxname])
        template = """{
    "name": "unix\/%s",
    "versions": [
        {
            "version": "%s",
            "providers": [
                {
                    "name": "%s",
                    "url": "%s",
                    "checksum_type": "sha1",
                    "checksum": "%s"
                }
            ]
        }
    ]
}
        """ % (self.vm_name, self.version, self.provider, url, checksum)
        with open(os.path.join(self.work_dir, "metadata.json"), "w") as metadata:
            metadata.write(template)

    def create_vagrant_template(self):
        STREAM.info("==> Creating Vagrantfile...")
        template = """
Vagrant::Config.run do |config|
  # This Vagrantfile is auto-generated by `vagrant package` to contain
  # the MAC address of the box. Custom configuration should be placed in
  # the actual `Vagrantfile` in this box.
  config.vm.base_mac = "0800274B29D3"
end

# Load include vagrant file if it exists after the auto-generated
# so it can override any of the settings
include_vagrantfile = File.expand_path("../include/_Vagrantfile", __FILE__)
load include_vagrantfile if File.exist?(include_vagrantfile)
"""
        with open(os.path.join(self.tmp_dir, "Vagrantfile"), "w") as vagrant_file:
            vagrant_file.write(template)

    def export_vm_configuration(self):
        STREAM.info("==> Exporting configuration...")
        STREAM.debug(" -> vagrant catalog directory: %s" % self.vagrant_catalog)
        if not os.path.exists(self.vagrant_catalog):
            STREAM.critical(" -> Vagrant catalog (%s) directory does not exist" % self.vagrant_catalog)
            STREAM.warning(" -> Export, passed...")
            return False
        self.work_dir = os.path.join(self.vagrant_catalog, self.vm_name)
        self.tmp_dir = os.path.join(self.vagrant_catalog, self.vm_name, "tmp")
        try:
            os.makedirs(self.tmp_dir)
        except OSError as errno:
            if "Errno 17" in str(errno):
                STREAM.info("==> Temporary directory detected, cleaning before start...")
                shutil.rmtree(self.tmp_dir)
                os.makedirs(self.tmp_dir)
            else:
                STREAM.error(errno)
                return False
        Popen('VBoxManage export %s --output %s' % (self.vm_name, os.path.join(self.tmp_dir, self.vm_name + ".ovf")),
              shell=True, stdout=sys.stdout, stderr=sys.stdout).communicate()
        for fil in os.listdir(self.tmp_dir):
            if fil.endswith(".vmdk"):
                os.rename(os.path.join(self.tmp_dir, fil), os.path.join(self.tmp_dir, "box-disk.vmdk"))
            elif fil.endswith(".ovf"):
                os.rename(os.path.join(self.tmp_dir, fil), os.path.join(self.tmp_dir, "box.ovf"))
        return True

    def renew_vm(self):
        for fil in os.listdir(self.work_dir):
            if fil.endswith(".box"):
                STREAM.info("==> Renew old box...")
                os.remove(os.path.join(self.work_dir, fil))
        os.rename(os.path.join(self.work_dir, self.boxname), os.path.join(self.work_dir, self.boxname[:-5]))



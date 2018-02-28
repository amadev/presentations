import random
import sys
import time
import uuid
import subprocess
import logging


LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
LOGGER.addHandler(ch)


NETWORK = 'test'
IMAGE = 'xenial'
PORT = 'sriov-port-%s' % uuid.uuid4()
FLAVOR = 'm1.small.sriov'
VM = 'sriov-vm-%s' % uuid.uuid4()


def wait_for_status(vm_id, target, sleep_time=3):
    cmd = 'nova show --minimal %s | grep "\ status\ " | awk \'{ print $4 }\'' % vm_id
    retries = 10
    while retries > 0:
        status = subprocess.check_output(cmd, shell=True).strip()
        if status == target:
            return True
        elif status == 'ERROR':
            raise ValueError('instance got error status')
        time.sleep(sleep_time)
        retries -= 1
    raise ValueError('instance status waiting timeout')



def main(n):
    for _ in range(n):
        from_host = random.choice([1, 2])
        to_host = 3 - from_host
        LOGGER.debug('start')
        cmd = 'openstack network show %s | grep "\ id\ " | awk \'{ print $4 }\'' % NETWORK
        net_id = subprocess.check_output(cmd, shell=True).strip()
        cmd = ('openstack port create --network %s --vnic-type direct %s'
               '| grep "\ id\ " | awk \'{ print $4 }\'') % (net_id, PORT)
        port_id = subprocess.check_output(cmd, shell=True).strip()
        cmd = 'openstack port show %s | grep "\ mac_address\ " | awk \'{ print $4 }\'' % port_id
        mac = subprocess.check_output(cmd, shell=True).strip()
        LOGGER.debug('port created id: %s mac: %s', port_id, mac)
        cmd = ('openstack server create --flavor %s --image %s --nic port-id=%s '
               '--availability-zone nova:cmp00%s --user-data user-data.txt %s '
               '| grep "\ id\ " | awk \'{ print $4 }\'') % (
                   FLAVOR, IMAGE, port_id, from_host, VM)
        vm_id = subprocess.check_output(cmd, shell=True).strip()
        wait_for_status(vm_id, 'ACTIVE')
        LOGGER.debug('vm created id: %s host cmp00%s', vm_id, from_host)
        cmd = 'nova migrate %s' % vm_id
        subprocess.check_output(cmd, shell=True).strip()
        LOGGER.debug('migration started')
        wait_for_status(vm_id, 'VERIFY_RESIZE', 10)
        cmd = 'nova resize-confirm %s' % vm_id
        subprocess.check_output(cmd, shell=True).strip()
        wait_for_status(vm_id, 'ACTIVE')
        LOGGER.debug('migration ended')
        cmd = 'nova show %s | grep "\ OS-EXT-SRV-ATTR:host\ " | awk \'{ print $4 }\'' % vm_id
        host = subprocess.check_output(cmd, shell=True).strip()
        assert host == 'cmp00%s' % to_host
        cmd = 'nova delete %s' % vm_id
        subprocess.check_output(cmd, shell=True).strip()
        cmd = 'openstack port delete %s' % port_id
        subprocess.check_output(cmd, shell=True).strip()
        LOGGER.debug('ok')


if __name__ == '__main__':
    main(1)

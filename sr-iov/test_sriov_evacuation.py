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


cmd = 'openstack network show %s | grep "\ id\ " | awk \'{ print $4 }\'' % NETWORK
net_id = subprocess.check_output(cmd, shell=True).strip()
cmd = ('openstack port create --network %s --vnic-type direct %s'
       '| grep "\ id\ " | awk \'{ print $4 }\'') % (net_id, PORT)
port_id = subprocess.check_output(cmd, shell=True).strip()
cmd = 'openstack port show %s | grep "\ mac_address\ " | awk \'{ print $4 }\'' % port_id
mac = subprocess.check_output(cmd, shell=True).strip()
LOGGER.debug('port created id: %s mac: %s', port_id, mac)
cmd = ('openstack server create --flavor %s --image %s --nic port-id=%s '
       '--availability-zone nova:cmp001 --user-data user-data.txt %s '
       '| grep "\ id\ " | awk \'{ print $4 }\'') % (
           FLAVOR, IMAGE, port_id, VM)
vm_id = subprocess.check_output(cmd, shell=True).strip()
wait_for_status(vm_id, 'ACTIVE')
LOGGER.debug('vm created %s', vm_id)
cmd = "nova service-force-down $(nova service-list | grep cmp001 | grep nova-compute | awk '{print $2}')"
subprocess.check_output(cmd, shell=True).strip()
cmd = 'nova evacuate %s' % vm_id
subprocess.check_output(cmd, shell=True).strip()
LOGGER.debug('evacuation started')
wait_for_status(vm_id, 'ACTIVE')
LOGGER.debug('evacuation ended')
cmd = 'nova show %s | grep "\ OS-EXT-SRV-ATTR:host\ " | awk \'{ print $4 }\'' % vm_id
host = subprocess.check_output(cmd, shell=True).strip()
assert host == 'cmp002'
LOGGER.debug('host checked')
cmd = 'nova delete %s' % vm_id
subprocess.check_output(cmd, shell=True).strip()
cmd = 'openstack port delete %s' % port_id
subprocess.check_output(cmd, shell=True).strip()
cmd = "nova service-force-down $(nova service-list | grep cmp001 | grep nova-compute | awk '{print $2}') --unset"
subprocess.check_output(cmd, shell=True).strip()
LOGGER.debug('ok')

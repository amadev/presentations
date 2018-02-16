import time
import uuid
import subprocess


NETWORK = 'test'
IMAGE = 'xenial'
PORT = 'sriov-port-%s' % uuid.uuid4()
FLAVOR = 'm1.extra_tiny'
VM = 'sriov-vm-%s' % uuid.uuid4()


def wait_for_status(vm_id, target, sleep_time=1):
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


cmd = 'neutron net-show %s | grep "\ id\ " | awk \'{ print $4 }\'' % NETWORK
net_id = subprocess.check_output(cmd, shell=True).strip()
cmd = ('neutron port-create %s --name %s --binding:vnic_type direct '
       '| grep "\ id\ " | awk \'{ print $4 }\'') % (net_id, PORT)
port_id = subprocess.check_output(cmd, shell=True).strip()
print('!port_id', type(port_id), port_id)
cmd = 'neutron port-show %s | grep "\ mac_address\ " | awk \'{ print $4 }\'' % port_id
mac = subprocess.check_output(cmd, shell=True).strip()
print('!mac', type(mac), mac)
cmd = ('openstack server create --flavor %s --image %s --nic port-id=%s '
       '--availability-zone nova:cmp001 --user-data user-data.txt %s '
       '| grep "\ id\ " | awk \'{ print $4 }\'') % (
           FLAVOR, IMAGE, port_id, VM)
vm_id = subprocess.check_output(cmd, shell=True).strip()
print('!vm_id', type(vm_id), vm_id)
wait_for_status(vm_id, 'ACTIVE')
print 'vm ACTIVE'
cmd = 'nova migrate %s' % vm_id
subprocess.check_output(cmd, shell=True).strip()
wait_for_status(vm_id, 'VERIFY_RESIZE', 10)
print 'vm VERIFY_RESIZE'
cmd = 'nova resize-confirm %s' % vm_id
subprocess.check_output(cmd, shell=True).strip()
wait_for_status(vm_id, 'ACTIVE')
print 'vm ACTIVE'
cmd = 'neutron port-show %s | grep "\ mac_address\ " | awk \'{ print $4 }\'' % port_id
mac = subprocess.check_output(cmd, shell=True).strip()
print('!mac', type(mac), mac)
cmd = 'nova show %s | grep "\ OS-EXT-SRV-ATTR:host\ " | awk \'{ print $4 }\'' % vm_id
host = subprocess.check_output(cmd, shell=True).strip()
assert host == 'cmp002'
print 'host checked'
cmd = 'nova delete %s' % vm_id
subprocess.check_output(cmd, shell=True).strip()
cmd = 'neutron port-delete %s' % port_id
subprocess.check_output(cmd, shell=True).strip()
print 'ok'

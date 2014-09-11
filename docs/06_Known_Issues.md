There are a small number of long-term issues, related to both the general design of Intel� DPDK vSwitch and outstanding bugs. These are detailed below.

______

## Intel� DPDK vSwitch

* To view a list of known bugs, or log a new one, please visit the [Issues][ovdk-issues] section of the Intel� DPDK vSwitch GitHub page.

* This release supports Intel� DPDK v1.7.1 only. Intel� DPDK v1.7.0 exhibits issues with IVSHMEM and is therefore unsupported.

* Intel� Virtualization Technology for Directed I/O (Intel� VT-d) should be disabled in the BIOS settings, unless PCI passthrough is required, in which case the following options should be added to the kernel boot parameters:

    ```
    intel_iommu=on iommu=pt
    ```

* When starting the VMs, the following warning may appear:

    ```bash
    (ASLR) is enabled in the kernel. This may cause issues with mapping memory into secondary processes.
    ```

    Although in most cases this warning is harmless, to suppress it, run the following command:

    ```bash
    echo 0 > /proc/sys/kernel/randomize_va_space
    ```

* This release has not been tested or validated for use with Virtual Functions, although it should theoretically work with Intel� DPDK 1.7.0.

* If testing performance with TCP, variances in performance may be observed; this variation is due to the protocol's congestion-control mechanisms. UDP produces more reliable and repeatable results, and it is the preferred protocol for performance testing.

* On start-up, Intel� DPDK vSwitch may issue an error:

    ```bash
    EAL: memzone_reserve_aligned_thread_unsafe(): memzone
    <RG_MP_log_history> already exists
    RING: Cannot reserve memory
    ```

    When an Intel� DPDK process starts, it attempts to reserve memory for various rings through a call to `rte_memzone_reserve`; in the case of a Intel� DPDK primary process, the operation should succeed, but for a secondary process, it is expected to fail, as the memory has already been reserved by the primary process. The particular ring specified in the error message - `RG_MP_log_history` - does not affect operation of the secondary process, so this error may be disregarded.

* On start-up, `ovs-dpdk` may complain that no ports are available (when using an Intel� DPDK-supported NIC):

    ```bash
    Total ports: 0

    EAL: Error - exiting with code: 1
    Cause: Cannot allocate memory for port tx_q details
    ```

    These error messages indicate that Intel� DPDK initialization failed because it did not detect any recognized physical ports. One possible cause is that the NIC is still driven by the default ixgbe driver. To resolve this issue, run `DPDK/tools/dpdk_nic_bind.py` before starting ovs-dpdk. (This process lets the Intel� DPDK poll mode driver take over the NIC.)

    For example, `dpdk_nic_bind.py -b igb_uio <PCI ID of NIC port>` binds the NIC to the Intel� DPDK igb_uio driver.

* Some Intel� DPDK dpif unit tests create files in `/tmp` (specifically, dpdk_flow_table and dpif_dpdk_vport_table). These are not always removed after iterations of the tests, causing subsequent tests to fail. These should be deleted manually in this case.

* Port deletion in the datapath is not fully supported. For this release, a temporary workaround is in place which disables deletion such that ports which have been used cannot be used again. A more permanent solution for this issue is currently in progress.

______

## Intel� DPDK vSwitch Sample Guest Application

In the current IVSHM implementation, multiple Intel� DPDK objects (memory zones, rings, and memory pools) can be shared between different guests. The host application determines what to share with each guest. The guest applications are not Intel� DPDK secondary processes anymore, and so they can create their own Intel� DPDK objects as well.

______

## Open vSwitch Testsuite

Open vSwitch contains a number of unit tests that collectively form the OVS "testsuite". While the majority of these tests currently pass without issue, a small number do fail. The common cause of failure for these tests is a discrepancy in the command line arguments required by many of the utilities in standard Open vSwitch and their equivalents in Intel� DPDK vSwitch. In addition, test three (3) causes the testsuite to hang and should be skipped. These issues will be resolved in a future release.

Many of the tests also fail due to differences in the required parameters for utilities such as `ovs-dpctl` (that is, Intel� DPDK vSwitch's version of these utilities require EAL parameters). As a result, these tests should be used as guidelines only.

In addition to the standard unit tests, Intel� DPDK vSwitch extends the testsuite with a number of "Intel� DPDK vSwitch"-specific unit tests. These tests require root privileges to run, due to the use of hugepages by the Intel� DPDK library. These tests are currently the only tests guaranteed to pass, with the exception of the `port-del` and `multicore-port-del` unit tests, as described earlier in this document.

______

## ovs-vswitchd

Not all functionality that is supported by Open vSwitch is supported by the Intel� DPDK vSwitch.

______

## ovs-vsctl

Not all functionality that is supported by Open vSwitch is supported by the Intel� DPDK vSwitch.

______

## ovs-ofctl

Not all functionality that is supported by Open vSwitch is supported by the Intel� DPDK vSwitch.

______

## ovs-dpctl

Not all functionality that is supported by Open vSwitch is supported by the Intel� DPDK vSwitch.

______

## ovs-ivshm-mngr

The IVSHM manager utility must be executed once the switch is up and running and not before. An attempt to share Intel� DPDK objects using the IVSHM manager utility before the switch has finished with its setup/init process may cause undesired behavior.

______

� 2014, Intel Corporation. All Rights Reserved

[ovdk-issues]: https://github.com/01org/dpdk-ovs/issues

# pam_netns

## what is this

Simple demonstration applying pre-configured network namespaces to user session using Pluggable Authentication Modules.

### Awesome/awful, should I use it

Probably not.

## requirements

`pam_python`

## Example

Configure a network namespace using `ip netns`:

    ip netns add ns0
    
    # loopback up
    ip netns exec ns0 ip link set dev lo up

 *NOTE:* By default namespaces configured with `ip netns` are not preserved across reboots. You need to write your own script to restore them on boot.

Place configuration in `/etc/security/pam_netns.conf`. Configuration file contains one username and network namespace name per line. To map user *test* to *ns0*:

    test ns0

Enable for session, for debian based distributions add to the end of `/etc/pam.d/common-session`:

    optional pam_python.so /etc/secirity/pam_python/pam_netns.py

Possible options:
   
   * `config=<path>` use alternative location for configuration file. Default: `/etc/security/pam_netns.conf`
   * `log=<path>` additional logging to a separate log. Default: empty (no logging)
   * `debug` more verbose logging
   
## Bugs

When using `sudo`, `su` etc., the network namespace is not changd back to default (pid 1) one.

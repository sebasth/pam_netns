#
# pam_netns.py
# 
# somewhat based on Linux iproute2's netns_switch() in lib/namespace.c
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version
# 2 of the License, or (at your option) any later version.
#

import ctypes
import os

libc = ctypes.cdll.LoadLibrary("libc.so.6")

path_config = "/etc/security/pam_netns.conf"
enable_debug = False

def value(arg):
    res = arg.split("=", 1)
    return "" if len(res) < 2 else res[1]

def parse_args(argv):
    global path_config
    global enable_debug
    
    for arg in argv:
        if arg.startswith("config="):
            path_config = value(arg)
    
        if arg.startswith("log="):
            open_log(value(arg))
    
        if arg == "debug":
            enable_debug = True

def parse_config():
    user_mapping = {}
    
    with open(path_config, "r") as f:
        debug("config: " + path_config)
        for line in f:
            (user, ns) = line.split(None, 1)
            ns = ns.strip()
            user_mapping[user] = ns
            debug("added mapping: %s, %s" % (user, ns.strip()))
            
    return user_mapping

def cleanup():
    close_log()

def pam_sm_open_session(pamh, flags, argv):
    try:
        parse_args(argv)
        user_mapping = parse_config()
    
        try:
            username = pamh.get_user()
        except pamh.exception:
            critical("couldn't get user from PAM")
            return pamh.PAM_SESSION_ERR
    
        if username in user_mapping:
            ns = user_mapping[username]
            if netns_switch_by_name(ns) < 0:
                return pamh.PAM_SESSION_ERR
            
            info("succesfully changed network namespace to \"%s\"" % ns)

        return pamh.PAM_SUCCESS
 
    except Exception as e:
        critical("error: %s" % str(e))
        return pamh.PAM_SESSION_ERR

    finally:
        cleanup()
        
def pam_sm_close_session(pamh, flags, argv):
    return pamh.PAM_SUCCESS

#
# NETNS
#
NET_PATH = "/var/run/netns"

# http://elixir.free-electrons.com/linux/v4.13/source/include/uapi/linux/sched.h#L29
CLONE_NEWNET = 0x40000000
CLONE_NEWNS  = 0x00020000

def netns_switch_by_name(name):
    return netns_switch_by_path(os.path.join(NET_PATH, name))

def netns_switch_by_path(path):
    try:
        f = open(path, "r")
        
    except Exception as e:
        critical("cannot open network namespace in \"%s\": %s" % (path, str(e)))
        return -1

    try:
        fd = f.fileno()
        err = libc.setns(fd, CLONE_NEWNET)
        if err < 0:
            critical("setting the network namespace \"%s\" failed: %s" % (path ,err))
            return -1

        # should unshare mount namespace?
        
        return 0

    finally:
        f.close()

#
# LOGGING
#

import datetime
fd_log = None

def now():
    return str(datetime.datetime.now())

def open_log(path):
    global fd_log
    fd_log = open(path, "a")
    
def close_log():
    global fd_log
    
    if fd_log:
        fd_log.flush()
        fd_log.close()
    
    fd_log = None
    
def critical(msg):
    if fd_log:
        fd_log.write("%s : critical : %s\n" % (now(), msg))

def info(msg):
    if fd_log:
        fd_log.write("%s : info     : %s\n" % (now(), msg))
        
def debug(msg):
    if fd_log and enable_debug:
        fd_log.write("%s : debug    : %s\n" % (now(), msg))    
        

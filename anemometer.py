#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import usb.core  # pyusb
import usb.util  # pyusb
import collections, platform

class anemometer(object):
    VENDOR_ID = 0x64BD
    PRODUCT_ID = 0x74E3
    rd_cmd = [0xb3, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    dl_cmd = [0xc4, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

    def __init__(self):
        self.open()

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, trace):
        self.close()

    def open(self):
        device = usb.core.find(idVendor=anemometer.VENDOR_ID, idProduct=anemometer.PRODUCT_ID)
        if device is None:
            raise OSError('Device not found')
        self._dev = device

        # Detach usbhid
        if not platform.platform().lower().startswith("windows"):
            c = 1
            for config in device:
                print('Detach usbhid: config', c, end="")
                print('Interfaces', config.bNumInterfaces, end="")
                for i in range(config.bNumInterfaces):
                    if device.is_kernel_driver_active(i):
                        device.detach_kernel_driver(i)
                    print(i, end="")
                c+=1
            print()

        # set the active configuration. With no arguments, the first
        # configuration will be the active one
        device.set_configuration()

        # get an endpoint instance
        cfg = device.get_active_configuration()
        intf = cfg[(0,0)]

        # end points
        try:
            epo = usb.util.find_descriptor(
                intf,
                # match the first OUT endpoint
                custom_match = \
                lambda e: \
                    usb.util.endpoint_direction(e.bEndpointAddress) == \
                    usb.util.ENDPOINT_OUT)
            assert epo is not None

            epi = usb.util.find_descriptor(
                intf,
                # match the first IN endpoint
                custom_match = \
                lambda e: \
                    usb.util.endpoint_direction(e.bEndpointAddress) == \
                    usb.util.ENDPOINT_IN)
            assert epi is not None
            
        except:
            self.close()
            raise OSError('Could not open end-points')
        self._epo,self._epi = epo,epi
        self._dev_is_open = True

    def close(self):
        if not self.is_open():
            return  # do nothing

        try:
            self._dev.reset()
            self._dev_is_open = False
        except usb.core.USBError as e:
            if e.errno != 19:   # ignore [Errno 19] No such device (it may have been disconnected)
                raise

    def is_open(self):
        return self._dev_is_open

    def _float24(self, x):
        return (x[1] + 256*x[0] ) * (10**(x[2]-256 if x[2] > 127 else x[2] ) )

    def _parse(self, data):
        if len(data) != 8:
            return None
        val_1 = self._float24(data[2:] )
        val_2 = self._float24(data[5:] )

        setting = collections.OrderedDict()
        is_vel = 0x80 & data[0]
        setting['flw_vel'] = "VEL"     if is_vel else "FLOW"
        setting['deg'] =     "C"       if 0x20 & data[0] else "F"
        setting['mph'] =     "mph"     if 0x10 & data[0] and is_vel else ""
        setting['knot'] =    "knot"    if 0x08 & data[0] and is_vel else ""
        setting['ft/min'] =  "ft/min"  if 0x04 & data[0] and is_vel else ""
        setting['kmh'] =     "km/h"    if 0x02 & data[0] and is_vel else ""
        setting['m/s'] =     "m/s"     if 0x01 & data[0] and is_vel else ""

        setting['max'] =      "max"    if 0x80 & data[1] else ""
        setting['min'] =      "min"    if 0x40 & data[1] else ""
        setting['avg'] =      "avg"    if 0x20 & data[1] else ""
        setting['2/3'] =      "2/3"    if 0x10 & data[1] else ""
        setting['cmm_cfm'] =  "" if is_vel else ("CFM"    if 0x08 & data[1] else "CMM")
        setting['hold'] =     "hold"   if 0x02 & data[1] else ""

        return val_1, val_2, setting

    def get_current(self):
        if not self.is_open():
            try:
                self.open()
                return self.get_current()
            finally:
                self.close()

        self._epo.write(anemometer.rd_cmd)
        data = self._epi.read(8,100)
        v1, v2, s = self._parse(data)
        return data, v1, v2, s

    def open_records(self):
        if not self.is_open():
            try:
                self.open()
                return self.open_records()
            finally:
                self.close()

        self._epo.write(anemometer.dl_cmd)

    def get_a_record(self):
        try:
            data = self._epi.read(8,100)
            v1, v2, s = self._parse(data)
            return data, v1, v2, s
        except usb.core.USBTimeoutError:
            return None

    def format_setting(self, setting, min_width=6):
        v1_unit = (
            (
                setting['mph'] +
                setting['knot'] +
                setting['ft/min'] +
                setting['kmh'] +
                setting['m/s']
            )if setting['flw_vel'] == "VEL" else setting['cmm_cfm'] )
        v2_unit = 'deg-' + setting['deg']
        out = []
        for k,v in setting.items():
            out.append(("%%%ds"%min_width)%v)
        return ','.join(out), v1_unit, v2_unit

if __name__ == '__main__':
    # Basic test 1 -- get current status
    with anemometer() as a:
        data, v1, v2, s = a.get_current()
        sttng, v1u, v2u = a.format_setting(s, 1)
        print("%6g [%s] %6g [%s] (%s)"%(v1, v1u, v2, v2u, sttng) )

    # Basic test 2 -- retrieve records
    print("\nRetrieving records...")
    with anemometer() as a:
        a.open_records()
        n = 1
        while True:
            res = a.get_a_record()
            if not res:
                break
            data, v1, v2, s = res
            sttng, v1u, v2u = a.format_setting(s, 1)
            print("%3d: %6g [%s] %6g [%s] (%s)"%(n, v1, v1u, v2, v2u, sttng) )
            n += 1

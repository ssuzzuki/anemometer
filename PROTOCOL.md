# Digital Hot Wire anemometer USB protocol description

## Interface description

Interface is recognised as a **HID** with **two endpoints**. One **in** and one **out**. Both work via **URB interruptions** with **8 bytes packet data length**.

## Ask for current state

To ask for current state, send `URB_INTERRUPT out` to endpoint **2** with capture data command `b3 00 00 00 00 00 00 00`.  Then you will receive `URB_INTERRUPT in` from endpoint **1** with data described below.

###example capture data:
`a1 00 00 00 fd 00 e5 ff` - 8bytes = 64bits

## Download recorded measurements

To download the recorded measurements, send `URB_INTERRUPT out` to endpoint **2** with download data command `c4 00 00 00 00 00 00 00`.  Then receive `URB_INTERRUPT in` from endpoint **1** repeatedly.  You will get the data with the same structure as above.  The reception times out when there are no more measurements available.

## Decode data

`URB_INTERRUPT in` have the last captured data with the following structure:

`[settings:2bytes][value1:3bytes][value2:3bytes]` - 8bytes = 64bits

### Decode `values`
Convert values to float as below:

 `float value = (256*byte0 + byte1)*(10^byte2)` -  Note: byte0 and byte1 are unsigned, and byte2 is signed.

### Decode `settings`
Settings have the following structure:

```
byte0
    bit7 (MSB):  FLOW/VEL
    bit6:        not used
    bit5:        deg-F/deg-C
    bit4:        VEL unit4 (mph)
    bit3:        VEL unit3 (knot)
    bit2:        VEL unit2 (ft/min)
    bit1:        VEL unit1 (km/h)
    bit0 (LSB):  VEL unit0 (m/s)

byte1
    bit7 (MSB):  MAX
    bit6:        MIN
    bit5:        AVG
    bit4:        2/3
    bit3:        Flow uit (CMM/CFM)
    bit2:        not used
    bit1:        HOLD
    bit0 (LSB):  not used
```

### Example 1
#### data:
`a1 00 05 a7 fd 00 fe ff`
#### decode:
 * `value1`: 
   * `0x05`=`5`, `0xa7`=`167` and `0xfd`=`-3` 
   * (256*`5` + `167`)*(10^`-3`) = 1.447
 * `value2`: 
   * `0x00`=`0`, `0xfe`=`254` and `0xff`=`-1` 
   * (256*`0` + `254`)*(10^`-1`) = 25.4
 * `setting` byte0 = `0xa1`=`0b10100001`
   * bit7=`1`=VEL
   * bit5=`1`=deg-C (value2 unit)
   * bit[4..0]=`00001`=m/s (value1 unit)
 * `setting` byte1 = `0x00`=`0b00000000`
   * bit[7..4]=`0000`=neither of MAX, MIN, AVG nor 2/3 selected
   * don't care bit3 because not in Flow mode
   * bit2=`0`=HOLD not selected

### Example 2
 33   2   4 204 254   0 123 253  0x21 0x02 0x04 0xcc 0xfe 0x00 0x7b 0xfd  12.280  0.1
#### data:
`21 02 04 cc fe 00 7b fd`
#### decode:
 * `value1`: 
   * `0x04`=`4`, `0xcc`=`202` and `0xfe`=`-2` 
   * (256*`4` + `204`)*(10^`-2`) = 12.28
 * `value2`: 
   * `0x00`=`0`, `0x7b`=`123` and `0xfd`=`-3` 
   * (256*`0` + `123`)*(10^`-3`) = 0.123
 * `setting` byte0 = `0x21`=`0b00100001`
   * bit7=`0`=FLOW
   * bit5=`1`=deg-C
   * bit[4..0]: don't care because not in Vel mode
 * `setting` byte1 = `0x02`=`0b00000010`
   * bit[7..4]=`0000`=neither of MAX, MIN, AVG nor 2/3 selected
   * bit3=`0`=CMM (value1 unit, value2 unit=M^2)
   * bit2=`1`=HOLD not selected

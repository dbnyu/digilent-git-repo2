# Analog Discovery 2 Ultrasound Project

## Digilent Analog Discovery 2 Specs
- [Basic Specs & Pinout](https://digilent.com/reference/test-and-measurement/analog-discovery-2/specifications)
- [More Detailed Spec (including buffer sizes per internal instrument)](https://digilent.com/reference/test-and-measurement/analog-discovery-2/start)

### USB Data Bandwidth & onboard Buffer Size

#### Onboard Memory Buffer
- the max buffer size for a single channel is 16k *samples*
  - scope & wavegen are 14-bit, but assuming data is stored/transported in full 2-Byte containers (TODO - TBD)
  - so 1 full buffer is 16k samples * 16 bits = 256,000 bits

#### USB Limitations
- [USB 2.0 limitations](https://forum.digilentinc.com/topic/18757-digilent-analog-discovery-2-record-mode-limiation/)
  - "The 480MHz is the USB 2.0 frequency, which uses some of this for sync and other usb protocol transfers, control... The maximum USB bulk IN bandwidth is about **40MBps, 370Mbps** for large data transfers. In the AD2 the bandwidth is **shared between various instruments**, so the **record is performed in small chunks which reduces the rate to about 1-2MHz**" (Attila - Digilent Engineer)

from serial.tools.list_ports import comports
from serial import Serial, PARITY_NONE, STOPBITS_ONE, EIGHTBITS
from pymodbus.client.sync import ModbusSerialClient
from enum import Enum


class PSU_Exception(Exception):
    pass


class PSU:
    """Instrument class for Longwei LW-3010EC and compatible
         Programmable Bench Power Supply.

    Args:
        * com_port (str): port name
        * slaveaddress (int): slave address in the range 1 to 247
        *     Factory default of 1
        *     Address of 0 is broadcast
        *     Set multiple supplies voltage and current supported


    Serial parameters: 9600,8,N,1

    Modbus Registers
    ----------------------------------------------------
    | Addr |    Name    |    Description    |Range |R/W|
    +------+------------+-------------------+------+---+
    |0x1000|   Set-U    |Voltage Setting    |0-32.0| W |
    |0x1001|   Set-I    |Current Setting    |0-10.5| W |
    |0x1002|     U      |Voltage Out        |0-32.0| R |
    |0x1003|     I      |Current Out        |0.10.5| R |
    |0x1004|  Run-Stop  |Output Relay On/Off| 0,1  | R |
    |0x1005|  CC-CV-OC  |Regulation Mode    | 0,1,2| R |
    |0x1006|Set-Run-Stop|Set Output Relay   | 0,1  | W |
    |0x1008|Set-Address |Set Slave Address  | 0-127| W |
    ----------------------------------------------------

    """

    class Registers(Enum):
        U_WRITE = 0x1000
        I_WRITE = 0x1001
        U_READ = 0x1002
        I_READ = 0x1003
        RUNSTOP_READ = 0x1004
        CC_CV_OC_READ = 0x1005
        RUNSTOP_WRITE = 0x1006
        ADDRESS_WRITE = 0x1008

    class RegulationMode():
        CURRENT = 0
        VOLTAGE = 1
        OVERCURRENT_PROTECTION = 2

    class OutputState():
        ON = 0
        OFF = 1

    class RawLimits():
        VOLTAGE = 3000
        CURRENT = 1050

    def __init__(self, com_port=None, slave_id=0x1, debug=False):
        self.debug = debug
        self.slave_id = slave_id
        self.com_port = com_port
        if self.com_port is None:
            self.com_port = self.find_PSU_com_port()
        self.pymc = ModbusSerialClient(method='rtu',
                                       port=self.com_port,
                                       baudrate=9600,
                                       timeout=5)

    def find_PSU_com_port(self):
        """Searches for PSU USB COM port adapter"""

        adapter_ids = {
            "CH340": ("1A86", "7523"),
            "FT232": ("0403", "6001")
            # add other serial devices here if we find them
        }

        com_ports_list = list(comports())

        for port in com_ports_list:
            # Don't attempt to test against adapters that do not report VID and PID
            if port.vid and port.pid:
                for adapter in adapter_ids:
                    if ('{:04X}'.format(port.vid),
                            '{:04X}'.format(port.pid)) == adapter_ids[adapter]:
                        if self.debug:
                            print(
                                f'Found {port.manufacturer} adapter {adapter} on {port.device}'
                            )
                        # Use the last com port found
                        if self.com_port is None or port.device > self.com_port:
                            self.com_port = port.device

        if self.com_port is None:
            raise OSError('PSU not found')

        if self.debug:
            print(f'Attempting PSU on {self.com_port}')

        return self.com_port

    def write(self, address, value):
        rc = self.pymc.write_register(address.value, value, unit=self.slave_id)
        if rc.isError() and self.debug:
            print(address.name, rc.message)

    def read(self, address, len=1):
        rc = self.pymc.read_holding_registers(address.value,
                                              len,
                                              unit=self.slave_id)

        if rc.isError():
            if self.debug:
                print(address.name, rc.message)
            return None

        if len == 1:
            return rc.registers[0]
        else:
            return rc.registers

    @property
    def current(self):
        return self.read(PSU.Registers.I_READ) / 100

    @current.setter
    def current(self, amps):
        if amps < 0 or amps > self.RawLimits.CURRENT:
            raise PSU_Exception(
                f'Requested current set point [{amps/100}] out of range [{self.RawLimits.CURRENT/100}]'
            )

        self.write(PSU.Registers.I_WRITE, int(round(amps * 100)))

    @property
    def voltage(self):
        return self.read(PSU.Registers.U_READ) / 100

    @voltage.setter
    def voltage(self, volts):
        if volts < 0 or volts > self.RawLimits.VOLTAGE:
            raise PSU_Exception(
                f'Requested voltage set point [{volts/100}] out of range [{self.RawLimits.VOLTAGE/100}]'
            )

        self.write(PSU.Registers.U_WRITE, int(round(volts * 100)))

    @property
    def all_raw(self):
        return self.read(PSU.Registers.U_WRITE, len=6)


#    @all.setter
#    def all_raw(self, volts):
#        self.write(PSU.Registers.U_WRITE, int(round(volts * 100)))
#
#     def read_set_values_raw(self):
#         """Read the voltage/current setpoint values and return raw values"""
#         rval = self.read_registers(4096, number_of_registers=6)
#         set_u = rval[0]
#         set_i = rval[1]
#         return set_u, set_i

    @property
    def output(self):
        return False if self.read(PSU.Registers.RUNSTOP_READ) == 0 else True

    @output.setter
    def output(self, on):
        self.write(PSU.Registers.RUNSTOP_WRITE, int(on))

    def toggle_output(self):
        if self.output:
            self.output = False
        else:
            self.output = True

    def apply_set_points(self, values):
        """Set the voltage and current set points"""
        volts, amps, off_before_change, on_after_change = values

        # print(f"volts: {volts}, amps: {amps}, off_before_change: {off_before_change}, on_after_change: {on_after_change}")

        if off_before_change:
            self.output = False

        self.voltage = volts / 100
        self.current = amps / 100

        if on_after_change == True:
            self.output = True

if __name__ == '__main__':
    # Run some tests and output
    psu = PSU(debug=True)

    print(f'Output={psu.output}')
    print(f'Voltage={psu.voltage}V')
    print(f'Current={psu.current}A')
    all_raw_values = psu.all_raw
    print(all_raw_values)
    psu.toggle_output()
    print(f'Output={psu.output}')
    psu.output = False
    try:
        psu.apply_set_points(
            [psu.RawLimits.VOLTAGE + 10, psu.RawLimits.CURRENT, False, False])
    except PSU_Exception as e:
        print(e)

    try:
        psu.apply_set_points(
            [psu.RawLimits.VOLTAGE, psu.RawLimits.CURRENT + 10, False, False])
    except PSU_Exception as e:
        print(e)

    psu.voltage = 38

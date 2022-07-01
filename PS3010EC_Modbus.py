import minimalmodbus as mmb


class PS3010EC_Exception(mmb.ModbusException):
    """Exception class for Longwei LW-3010EC
         Programmable Bench Power Supply.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PS3010EC_Modbus(mmb.Instrument):
    """Instrument class for Longwei LW-3010EC
         Programmable Bench Power Supply.

    Args:
        * portname (str): port name
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
    |0x0001|   Set-I    |Current Setting    |0-10.5| W |
    |0x0002|     U      |Voltage Out        |0-32.0| R |
    |0x0003|     I      |Current Out        |0.10.5| R |
    |0x0004|  Run-Stop  |Output Relay On/Off| 0,1  | R |
    |0x0005|  CC-CV-OC  |Regulation Mode    | 0,1,2| R |
    |0x0006|Set-Run-Stop|Set Output Relay   | 0,1  | W |
    |0x0008|Set-Address |Set Slave Address  | 0-127| W |
    ----------------------------------------------------

    """

    REGULATION_MODE_CURRENT = 0
    REGULATION_MODE_VOLTAGE = 1
    REGULATION_MODE_OVERCURRENT_PROTECTION = 2

    MAXIMUM_VOLTAGE = 30
    MAXIMUM_CURRENT = 10.5

    MAX_U_RAW = 3000
    MAX_I_RAW = 1050

    def __init__(self, portname, debug=False):
        super().__init__(portname, 1)
        self.serial.baudrate = 9600
        self.serial.parity = mmb.serial.PARITY_NONE
        self.serial.stopbits = 1
        self.serial.timeout = 2
        self.debug = debug
        self.mode = mmb.MODE_RTU
        self.clear_buffers_before_each_transaction = True

    def read_status_raw(self):
        """Read all six registers that contain status information"""
        return self.read_registers(4096, 6)

    def read_set_values_raw(self):
        """Read the voltage/current setpoint values and return raw values"""
        rval = self.read_registers(4096, number_of_registers=6)
        set_u = rval[0]
        set_i = rval[1]
        return set_u, set_i

    def read_set_values(self):
        set_u, set_i = self.read_set_values_raw()
        set_u = set_u / 100
        set_i = set_i / 100
        return set_u, set_i

    def read_values(self):
        """Read the present voltage/current output values"""
        rval = self.read_registers(4098, 2)
        voltage = rval[0] / 100
        current = rval[1] / 100
        return voltage, current

    @property
    def is_output_on(self):
        """Read the output relay state (returns True/False)"""
        rval = self.read_registers(4100, 1)
        if rval[0] == 0:
            return False
        else:
            return True

    def set_output_on(self, new_state):
        """Set the output relay state (takes True/False)"""
        if new_state:
            self.write_register(4102, 1, functioncode=6)
        else:
            self.write_register(4102, 0, functioncode=6)

    def toggleRS(self):
        """Toggle the output relay state"""
        if self.is_output_on:
            self.set_output_on(False)
        else:
            self.set_output_on(True)

        return self.is_output_on

    def applySet(self, values):
        """Set the voltage and current set points"""
        SetU, SetI, off_before_change, on_after_change = values
        #print(f"SetU: {SetU}, SetI {SetI}, off_before_change: {off_before_change}, on_after_change: {on_after_change}")
        if SetU <= 0 or SetU >= self.MAX_U_RAW:
            raise PS3010EC_Exception(
                f'Requested voltage set point [{SetU/100}] out of range [{self.MAXIMUM_VOLTAGE}]'
            )

        if SetI <= 0 or SetI >= self.MAX_I_RAW:
            raise PS3010EC_Exception(
                f'Requested current set point [{SetI/100}] out of range [{self.MAXIMUM_CURRENT}]'
            )

        if off_before_change:
            self.set_output_on(False)

        self.write_registers(4096, [SetU, SetI])

        if on_after_change == True:
            self.set_output_on(True)

    @property
    def read_regulation_state(self):
        """Read the regulation state (0,1,2)"""
        rval = self.read_registers(4096, 6)
        return rval[5]

    def enable_overcurrent_protection(self):
        """enable overcurrent_protection"""
        #self.write_register(4101, 2, functioncode=6)
        # No modbus functions equivalent to pressing the OCP button on the front panel
        pass

    def disable_overcurrent_protection(self):
        """disable overcurrent_protection"""
        #self.write_register(4101, 1, functioncode=6)
        # No modbus functions equivalent to pressing the OCP button on the front panel
        pass

    def write_set_points(self,
                         set_u,
                         set_i,
                         OffBeforeChange=True,
                         OnAfterChange=False):
        """Set the voltage and current set points"""
        if set_u >= 0.0 and set_u <= self.MAXIMUM_VOLTAGE:
            raw_set_u = int(set_u * 100)
        else:
            raise PS3010EC_Exception(
                f'Requested voltage set point [{set_u}] out of range [{self.MAXIMUM_VOLTAGE}]'
            )

        if set_i >= 0.0 and set_i <= self.MAXIMUM_CURRENT:
            raw_set_i = int(set_i * 100)
        else:
            raise PS3010EC_Exception(
                f'Requested current set point [{set_i}] out of range [{self.MAXIMUM_CURRENT}]'
            )

            self.set_output_on(False)

        self.write_registers(4096, [raw_set_u, raw_set_i])


#        if OnAfterChange == True and not relay_state:
#            self.set_output_on(True)

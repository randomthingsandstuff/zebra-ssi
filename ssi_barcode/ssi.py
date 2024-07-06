import serial
import struct
from ssi_barcode import util
from collections import defaultdict


class SSIScanner:
    def __init__(self, device):
        self.device = device
        self._handlers = defaultdict(list)

    def add_handler(self, msg_type, handler):
        self._handlers[msg_type].append(handler)

    def handle_msg(self, msg):
        print(msg.xxd_dump())
        for handler in self._handlers[msg.type]:
            handler(msg)

    def run(self):
        with serial.Serial(self.device, 9600, rtscts=True) as serconn:
            t = ssi.SSITransport(ser)
            for msg in t.run():
                self.handle_msg(msg)


class SigScan:
    SYMBOLOGY = 0x69
    IMAGE_FORMAT_JPEG = 0x01
    IMAGE_FORMAT_BMP = 0x03
    IMAGE_FORMAT_TIFF = 0x04
    def __init__(self):
        self.image_format = None
        self.type = None
        self.length = None
        self.image_data = None

    @classmethod
    def decode_from_scan(cls, scan):
        decoder = util.BinaryDecoder(scan.data)
        msg = cls()
        if scan.symbology != cls.SYMBOLOGY:
            raise ValueError("Wrong symbology")
        msg.image_format = decoder.read_byte()
        msg.type = decoder.read_byte()
        msg.length = decoder.read_uint32_be()
        print("len: %s, data len %s" % (msg.length, len(scan.data)))
        msg.image_data = decoder.read_bytes(msg.length)
        #if not decoder.is_done():
        #    raise ValueError("data too long")
        return msg

        

class ScanMessage:
    OP_CODE = 0xf3
    
    def __init__(self):
        self.symbology = None
        self.aim_code = None
        self.data = b''
        self.decode = None

    def text_dump(self):
        xxd_data_dump = util.xxd_format(self.data)
        dump = f"symbology: {self.symbology}, AIM Code: {self.aim_code}\n"
        dump += f"Data:\n {xxd_data_dump}"
        return dump

    def decode_from_barcode_data(self, data):
        self.aim_code = data[:3]
        self.data = data[3:]
        if self.symbology == SigScan.SYMBOLOGY:
            self.decode = SigScan.decode_from_scan(self)

    @classmethod
    def decode_from_packets(cls, packets):
        done = False
        symbology = None
        msg = cls()
        data = b''
        for packet in packets:
            if done:
                raise ValueError("Got extra packets after done")
            if packet.opcode != ScanMessage.OP_CODE:
                raise ValueError("Wrong opcode for ScanMessage")
            if packet.msg_source != MSG_SOURCE_DEVICE:
                raise ValueError("Wrong message source")
            done = False if packet.status & PKT_STATUS_CONTINUATION else True
            pkt_symbology = packet.data[0]
            if msg.symbology is not None and pkt_symbology != msg.symbology:
                raise ValueError("Different symbology in continuation")
            msg.symbology = pkt_symbology
            data += packet.data[1:]
        if not done:
            raise ValueError("Packet stream incomplete")
        msg.decode_from_barcode_data(data)

        return msg




MSG_SOURCE_DEVICE = 0
MSG_SOURCE_HOST = 4

PKT_STATUS_CONTINUATION = 2

class Packet:
    LENGTH_SIZE = 1
    OPCODE_SIZE = 1
    MSG_SRC_SIZE = 1
    STATUS_SIZE = 1
    HEADER_SIZE = OPCODE_SIZE + MSG_SRC_SIZE + STATUS_SIZE
    CSUM_SIZE = 2

    def __init__(self):
        self.length = None
        self.opcode = None
        self.msg_source = None
        self.status = None
        self.data = None
        self.csum = None
        self._encoded = None

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name != '_encoded':
            super().__setattr__('_encoded', None)
    
    def xxd_dump(self):
        return util.xxd_format(self._encoded)

    def decode(self, raw_data):
            offs = 0

            self.length = raw_data[0]
            data_length = self.length - self.LENGTH_SIZE - self.HEADER_SIZE
            offs += self.LENGTH_SIZE

            self.opcode = raw_data[offs]
            offs += self.OPCODE_SIZE

            self.msg_source = raw_data[offs]
            offs += self.MSG_SRC_SIZE

            self.status = raw_data[offs]
            offs += self.STATUS_SIZE

            self.data = raw_data[offs:offs + data_length]
            offs += data_length

            self.csum = raw_data[offs:]
            #print("length: %s, opcode: %s, src: %s, status: %s, data: %s, csum: %s" \
            #        % (hex(self.length), self.opcode.hex(), self.msg_source.hex(), self.status.hex(), \
            #        self.data.hex(), self.csum.hex())) 
            calculated_csum = calc_csum(raw_data[:-2])
            print(calculated_csum.hex())
            if calculated_csum == self.csum:
                print("good checksum, send an ACK")
                self._encoded = raw_data
            else:
                print("bad horrible nogood checksum. send a NACK")
                raise ValueError("Bad checksum")


class SSITransport:
    LENGTH_SIZE = 1
    OPCODE_SIZE = 1
    MSG_SRC_SIZE = 1
    STATUS_SIZE = 1
    HEADER_SIZE = OPCODE_SIZE + MSG_SRC_SIZE + STATUS_SIZE
    CSUM_SIZE = 2

    opcode_decoders = {0xf3: ScanMessage}

    def __init__(self, serialdev):
        self.serialdev = serialdev

    def _get_packet(self):
            raw_data = self.serialdev.read(self.LENGTH_SIZE)
            length = raw_data[0]
            if length < 4:
                raise ValueError("Bad lenght received: %d", length)

            raw_data += self.serialdev.read(length - self.LENGTH_SIZE + self.CSUM_SIZE)
            packet = Packet()

            try: 
                packet.decode(raw_data)
                print("_get_packet good checksum, send an ACK")
                self._send_ack()
            except ValueError as e:
                #self._send_nack()
                return None 
            return packet


    def run(self):
        packets = []
        while True:
            packet = self._get_packet()
            if packet is None:
                continue
            if packets and packet.opcode != packets[0].opcode:
                raise ValueError("Change in opcode in the stream")
            packets.append(packet)
            if packet.status & PKT_STATUS_CONTINUATION == 0:
                msg = SSITransport.opcode_decoders[packet.opcode].decode_from_packets(packets)
                yield msg
                packets = []


    def _send_ack(self):
        data = b'\x04\xd0\x04\x00'
        data = data + calc_csum(data)
        self.serialdev.write(data)



class SSI_PDU:
    def __init__(self):
        self.length = None
        self.source = None
        self.retransmit = None
        self.continuation = None
        self.change_type = None
        self.data = None
        self.csum = None

    def decode(self):
        pass



class CMD_ACK:
    OPCODE = b'0xd0'


def calc_csum(data: bytes) -> bytes:
    # Sum all the bytes
    total = sum(data)
    
    # Limit the total to 16 bits
    total = total & 0xFFFF
    
    # Take the one's complement (invert all the bits)
    ones_complement = ~total & 0xFFFF
    
    # Add one to get the two's complement
    twos_complement = (ones_complement + 1) & 0xFFFF
    
    # Convert the result to 2 bytes in big-endian format
    checksum_bytes = struct.pack('>H', twos_complement)
    
    return checksum_bytes




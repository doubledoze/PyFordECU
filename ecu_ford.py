import serial, time, pynput, threading, signal, sys, termios, atexit
from select import select

ms_can = '/dev/ttyUSB0'
hs_can = '/dev/ttyUSB1'

def calculate_checksum(data):
    checksum = sum(data) & 0xFF
    return checksum

### INITIALISATION DES PORTS SERIES
hs_ser = serial.Serial(hs_can, baudrate=2000000, timeout=1)
ms_ser = serial.Serial(ms_can, baudrate=2000000, timeout=1)

init_frame_hs = [0xAA, 0x55, 0x12, 0x05, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00]
init_frame_ms = [0xAA, 0x55, 0x12, 0x07, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00]

checksum_hs = calculate_checksum(init_frame_hs)
checksum_ms = calculate_checksum(init_frame_ms)

init_frame_hs.append(checksum_hs)
init_frame_ms.append(checksum_ms)

init_frame_hs.append(0x55)
init_frame_ms.append(0x55)

buffer_hs = bytes(init_frame_hs)
buffer_ms = bytes(init_frame_ms)

hs_ser.write(buffer_hs)
ms_ser.write(buffer_ms)

time.sleep(0.5)
######################################

# Gestion du terminal, écho des touches
fd = sys.stdin.fileno()
oldterm = termios.tcgetattr(fd)

def set_term():
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)

def reset_term():
    termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)

set_term()
atexit.register(reset_term)
######################################

def send(can_device, id, data_string):
    try:
        # Choisissez le port série approprié en fonction de can_device
        if can_device == 'hs-can':
            ser = hs_ser
        elif can_device == 'ms-can':
            ser = ms_ser
        else:
            raise ValueError(f"Unknown CAN device: {can_device}")

        formatted_id = f"{int(id, 16):04X}"
        id_val = [int(formatted_id[2:], 16), int(formatted_id[:2], 16)]
        
        data_list = [int(byte_str, 16) for byte_str in data_string.split()]
        
        data_frame = [0xAA, 0xC8] + id_val + data_list + [0x55]

        ser.write(bytes(data_frame))
    
    except serial.SerialException as e:
        print("Serial communication error:", e)
    except Exception as e:
        print("Error:", e)


def display_keys(active_keys):
    """
    Affiche la liste des touches avec leur fonction.
    Si une touche est active, elle est sous-lignée.
    """
    # Efface l'écran
    print("\033c", end="")
    
    print("    ███████╗ ██████╗ ██████╗ ██████╗     ███████╗ ██████╗██╗   ██╗")
    print("    ██╔════╝██╔═══██╗██╔══██╗██╔══██╗    ██╔════╝██╔════╝██║   ██║")
    print("    █████╗  ██║   ██║██████╔╝██║  ██║    █████╗  ██║     ██║   ██║")
    print("    ██╔══╝  ██║   ██║██╔══██╗██║  ██║    ██╔══╝  ██║     ██║   ██║")
    print("    ██║     ╚██████╔╝██║  ██║██████╔╝    ███████╗╚██████╗╚██████╔╝")
    print("    ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═════╝     ╚══════╝ ╚═════╝ ╚═════╝ ")
    print("                                                ┓     ┏┳┓┓      ")
    print("                                                ┣┓┓┏   ┃ ┣┓┓┏┏┃┃")
    print("                                                ┗┛┗┫   ┻ ┛┗┗┻┗┗┫")
    print("                                                   ┛           ┛")
    print("                                                    @Samy SCANNA")
    print("                                                                ")

    for key, info in key_mappings.items():
        if key in active_keys:
            print(f"\033[92m\033[4m{key}\033[0m : {info['description']}")  # Vert et sous-ligné
        else:
            print(f"\033[91m{key}\033[0m : {info['description']}")  # Rouge

    # Réinitialiser la couleur à la fin
    print("\033[0m")


key_mappings = {
    'A': {
        'action': lambda: send("hs-can", "0x420", "80 00 00 00 10 00 11 CC"),
        'description': '[hs-can] Extinction des voyants moteur, huile, batterie + temp à 90°',
        'interval': 20
    },
    'Z': {
        'action': lambda: send("hs-can", "0x201", "03 84 00 00 00 00 C8 00"),
        'description': '[hs-can] Activation du ralenti moteur (900rpm - 0kmh)',
        'interval': 20
    },
    'E': {
        'action': lambda: send("hs-can", "0x212", "08 00 00 00 40 00 00 00"),
        'description': '[hs-can] Désactivation voyant ABS et antipatinage',
        'interval': 20
    },
    'R': {
        'action': lambda: send("ms-can", "0x460", "00 00 00 00 00 00 00 00"),
        'description': '[hs-can] Désactivation voyant airbag + ceinture',
        'interval': 20
    },
    'T': {
        'action': lambda: send("ms-can", "0x265", "20 00 00 00 00 00 00 00"),
        'description': '[ms-can] Clignontant gauche',
        'interval': 1000
    },
    'Y': {
        'action': lambda: send("ms-can", "0x265", "40 00 00 00 00 00 00 00"),
        'description': '[ms-can] Clignotant droit',
        'interval': 1000
    },
    'U': {
        'action': lambda: send("ms-can", "0xc80", "19 00 00 00 00 00 00 00"),
        'description': '[ms-can] Désactivation frein à main',
        'interval': 20
    },
    'Q': {
        'action': lambda: send("hs-can", "0x420", "80 00 00 00 41 00 11 CC"),
        'description': '[hs-can] Défaut moteur',
        'interval': 20
    },
    'S': {
        'action': lambda: send("hs-can", "0x201", "07 D0 00 00 3A 98 C8 00"),
        'description': '[hs-can] Vitesse',
        'interval': 20
    },
}

active_keys = set()
threads = {}

def threaded_send(key):
    while key in active_keys:
        key_mappings[key]['action']()
        time.sleep(key_mappings[key]['interval'] / 1000)

def on_press(key):
    try:
        # Convertir la touche en majuscule (pour gérer à la fois 'a' et 'A')
        key_char = key.char.upper()
        
        # Vérifier si la touche est dans key_mappings
        if key_char in key_mappings:
            if key_char in key_mappings:
                if key_char in active_keys:
                    active_keys.remove(key_char)
                    if key_char in threads:
                        threads[key_char].join()  # stop the thread
                        del threads[key_char]
                else:
                    active_keys.add(key_char)
                    t = threading.Thread(target=threaded_send, args=(key_char,))
                    t.start()
                    threads[key_char] = t

    except AttributeError:
        pass

    display_keys(active_keys)

def main():
    display_keys(active_keys)
    with pynput.keyboard.Listener(on_press=on_press) as listener:
        listener.join()

def sigint_handler(signum, frame):
    print("\nArrêt du calculateur...")
    print("Fermeture des liaisons CAN...\n")
    hs_ser.close()
    ms_ser.close()
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

if __name__ == "__main__":
    main()

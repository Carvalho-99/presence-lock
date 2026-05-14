"""
Presence Lock — Teste de detecção Bluetooth
============================================
Rode este script ANTES de usar o sistema para confirmar que o seu
iPhone está sendo detectado corretamente.

Uso:
    python test_detection.py

O que esperar:
  - "PRESENTE" a cada ~5s enquanto o iPhone estiver perto com BT ligado
  - "AUSENTE"  quando o BT for desligado ou o celular sair de alcance

Ctrl+C para parar.
"""

import socket
import time

AF_BTH = 32
BTPROTO_RFCOMM = 3
PRESENT_ERRORS = {10064, 10061}

try:
    from config import PHONE_MAC
except ImportError:
    print("ERRO: config.py não encontrado. Execute na pasta do projeto.")
    raise SystemExit(1)

if "XX:XX:XX:XX:XX:XX" in PHONE_MAC:
    print("ERRO: Preencha o PHONE_MAC no config.py com o MAC do seu iPhone.")
    print("       Ajustes → Geral → Informações → Bluetooth")
    raise SystemExit(1)


def detect(mac: str) -> tuple[bool, str]:
    sock = None
    try:
        sock = socket.socket(AF_BTH, socket.SOCK_STREAM, BTPROTO_RFCOMM)
        sock.settimeout(4.0)
        sock.connect((mac, 1))
        return True, "conectou"
    except OSError as e:
        w = getattr(e, "winerror", None)
        if w in PRESENT_ERRORS:
            return True, f"winerror={w}"
        return False, f"winerror={w}"
    finally:
        if sock:
            try:
                sock.close()
            except Exception:
                pass


def main():
    print(f"Monitorando: {PHONE_MAC}")
    print("iPhone perto com BT ligado → PRESENTE | BT desligado → AUSENTE")
    print("Ctrl+C para parar\n")

    while True:
        presente, detalhe = detect(PHONE_MAC)
        status = "✓ PRESENTE" if presente else "✗ AUSENTE "
        print(f"[{time.strftime('%H:%M:%S')}]  {status}  ({detalhe})")
        time.sleep(1)


if __name__ == "__main__":
    main()

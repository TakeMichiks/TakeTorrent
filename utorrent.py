import libtorrent as lt
import time
import sys
import os
from plyer import notification

# --- Definición de la ruta de descarga (CORRECTO) ---
if getattr(sys, 'frozen', False):
    # Si es un .exe, la base es el directorio donde está el .exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Si es un script .py normal, la base es el directorio del script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DOWNLOAD_BASEDIR = os.path.join(BASE_DIR, 'Downloads')

# Crea la carpeta de descargas si no existe
if not os.path.exists(DOWNLOAD_BASEDIR):
    os.makedirs(DOWNLOAD_BASEDIR)

def procesar_cola_de_descargas():
    """
    Función principal que gestiona la creación y descarga de una cola de torrents.
    """

    # --- 1. CREAR LA COLA DE DESCARGA ---
    links_en_cola = []
    print("\n--- Creador de Cola de Descarga ---")
    print("Pega el Enlace magnet y Preciona enter. Presiona Enter Estando vacia la Linea para Continuar.")
    
    while True:
        magnet_link = input("> ")
        if not magnet_link:
            break
        
        if magnet_link.startswith("magnet:?xt=urn:btih:"):
            links_en_cola.append(magnet_link)
            print(f"Añadido. Torrents en cola: {len(links_en_cola)}")
        else:
            print("Error: El texto no es un enlace magnet válido. Inténtalo de nuevo.")

    if not links_en_cola:
        print("No se añadió ningún torrent a la cola.")
        return

    # --- 2. MOSTRAR COLA Y PEDIR CONFIRMACIÓN ---
    print("\n--- Revisión de la Cola ---")
    print(f"Se van a descargar {len(links_en_cola)} torrent(s) en la carpeta 'Downloads':")
    for i, link in enumerate(links_en_cola, 1):
        print(f"  {i}. {link[:70]}...") 

    confirmacion = input("\n¿Iniciar la descarga de esta cola? (s/n): ").lower()
    if confirmacion != 's':
        print("Descarga cancelada por el usuario.")
        return

    # --- 3. PROCESAR LA COLA, UN TORRENT A LA VEZ ---
    save_path = DOWNLOAD_BASEDIR 
    ses = lt.session({'listen_interfaces': '0.0.0.0:6881'})

    for i, magnet_link in enumerate(links_en_cola, 1):
        print(f"\n--- Descargando Torrent {i} de {len(links_en_cola)} ---")
        
        params = lt.parse_magnet_uri(magnet_link)
        params.save_path = save_path
        handle = ses.add_torrent(params)

        print("Esperando metadatos...")
        while not handle.status().has_metadata:
            time.sleep(0.1)

        ti = handle.torrent_file()
        torrent_name = ti.name() if ti else "nombre desconocido"
        print(f"Descargando ahora: {torrent_name}")

        while not handle.status().is_seeding:
            s = handle.status()
            state_str = ['en cola', 'comprobando', 'descargando metadatos',
                         'descargando', 'finalizado', 'seeding', 'allocating', 'comprobando resume data']
            
            print(
                f"\rProgreso: {s.progress * 100:.2f}% | "
                f"Velocidad: {s.download_rate / 1000:.1f} kB/s | "
                f"Peers: {s.num_peers} | "
                f"Estado: {state_str[s.state]}",
                end="" 
            )
            time.sleep(1)
        
        print(f"\nDescarga de '{torrent_name}' completada.")

        # Intenta enviar una notificación y captura cualquier error para evitar que el programa se cierre.
        try:
            notification.notify(
                title='Descarga Completada',
                message=f"Se terminó la descarga de {torrent_name}",
                app_name='Gestor de Torrents',
                timeout=10
            )
        except Exception as e:
            print(f"\n--- ADVERTENCIA: No se pudo enviar la notificación de escritorio. Error: {e} ---")

    print("\n--- ¡Todos los torrents de la cola han sido descargados! ---")

# === BUCLE PRINCIPAL DEL PROGRAMA ===
while True:
    procesar_cola_de_descargas()
    
    repetir = input("\n¿Quieres iniciar una nueva cola de descargas? (s/n): ").lower()
    if repetir != 's':
        print("Programa finalizado.")
        break

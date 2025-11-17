# -*- coding: utf-8 -*-
"""
Bot de Kingshot - Version Headless con Logging
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sys
import logging
from datetime import datetime
import re

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_SCRAPING = True
except ImportError:
    HAS_SCRAPING = False


def fetch_active_gift_codes():
    if not HAS_SCRAPING:
        print("[ERROR] Necesitas instalar requests y beautifulsoup4:")
        print("        pip install requests beautifulsoup4")
        return []

    url = "https://kingshot.net/gift-codes"

    try:
        print("[*] Obteniendo codigos activos desde kingshot.net...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        all_text = soup.get_text()
        active_codes = []

        # Patron exacto: Active + codigo + (Copy o Expires)
        pattern = r'Active([A-Za-z0-9]{5,20})(?:Copy|Expires)'
        matches = re.findall(pattern, all_text)

        for code in matches:
            if code not in active_codes:
                active_codes.append(code)

        active_codes = list(dict.fromkeys(active_codes))[:20]
        if active_codes:
            print(f"[+] Encontrados {len(active_codes)} codigos activos:")
            for code in active_codes:
                print(f"    - {code}")
            return active_codes
        else:
            print("[!] No se encontraron codigos activos")
            return []

    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        return []

class KingshotBotHeadless:
    def __init__(self, player_id, headless=True):
        self.player_id = player_id
        self.url = "https://ks-giftcode.centurygame.com/"
        self.headless = headless

        # Configurar logging
        self.setup_logging()

        # Configurar Chrome
        options = webdriver.ChromeOptions()

        if headless:
            # Múltiples flags para asegurar modo headless
            options.add_argument('--headless=new')
            options.add_argument('--headless')  # Sintaxis antigua por compatibilidad
            options.add_argument('--disable-gpu')
            options.add_argument('--window-position=-2400,-2400')  # Fuera de pantalla
            self.log_info("Modo headless activado (navegador INVISIBLE)")
        else:
            self.log_info("Modo visible activado")

        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        # Suprimir logs de Chrome
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        self.log_info("Iniciando ChromeDriver...")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 20)
        self.log_success("ChromeDriver iniciado correctamente")

    def setup_logging(self):
        """Configura el sistema de logging"""
        # Crear nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"bot_log_{timestamp}.txt"

        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )

        self.logger = logging.getLogger(__name__)
        self.logger.info("="*70)
        self.logger.info("BOT DE CODIGOS DE REGALO - KINGSHOT")
        self.logger.info("="*70)
        self.logger.info(f"Archivo de log: {log_filename}")
        self.logger.info(f"Player ID: {self.player_id}")

    def log_info(self, msg):
        """Log nivel INFO"""
        self.logger.info(f"[*] {msg}")

    def log_success(self, msg):
        """Log de éxito"""
        self.logger.info(f"[+] {msg}")

    def log_error(self, msg):
        """Log de error"""
        self.logger.error(f"[ERROR] {msg}")

    def log_warning(self, msg):
        """Log de advertencia"""
        self.logger.warning(f"[!] {msg}")

    def log_debug(self, msg):
        """Log de debug"""
        self.logger.debug(f"[DEBUG] {msg}")

    def wait_for_vue(self):
        """Espera a que Vue.js termine de cargar"""
        self.log_info("Esperando a que Vue.js cargue...")
        time.sleep(3)
        self.wait.until(lambda d: len(d.find_element(By.ID, "app").text) > 0)
        time.sleep(1)
        self.log_success("Vue.js cargado correctamente")

    def find_all_clickables(self):
        """Encuentra todos los elementos clickeables"""
        clickables = []
        selectors = ["div[class*='btn']", "div[class*='button']", "button"]

        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed():
                        clickables.append(elem)
            except:
                continue

        return clickables

    def take_screenshot(self, name):
        """Toma un screenshot y registra en el log (DESACTIVADO)"""
        # Screenshots desactivados - no hacer nada
        pass

    def dismiss_modal(self):
        """Cierra cualquier modal o mascara que este bloqueando la interfaz"""
        try:
            self.log_info("Verificando si hay modal activo...")
            time.sleep(1)

            # Intentar encontrar y cerrar el modal
            # Metodo 1: Buscar boton de cerrar (X, OK, Close, etc)
            close_selectors = [
                "div[class*='close']",
                "button[class*='close']",
                "div[class*='btn-close']",
                "div[class*='modal'] button",
                "div[class*='dialog'] button"
            ]

            for selector in close_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in buttons:
                        if btn.is_displayed():
                            self.log_info(f"Encontrado boton de cerrar: {btn.text or 'sin texto'}")
                            btn.click()
                            time.sleep(1)
                            self.log_success("Modal cerrado con boton")
                            return True
                except:
                    continue

            # Metodo 2: Hacer clic en la mascara (mask) de fondo
            try:
                mask = self.driver.find_element(By.CSS_SELECTOR, "div.mask")
                if mask.is_displayed():
                    self.log_info("Encontrada mascara de fondo, haciendo clic para cerrar...")
                    mask.click()
                    time.sleep(1)
                    self.log_success("Modal cerrado haciendo clic en mascara")
                    return True
            except:
                pass

            # Metodo 3: Forzar cierre con JavaScript
            try:
                self.driver.execute_script("""
                    var masks = document.querySelectorAll('.mask, [class*="mask"]');
                    masks.forEach(function(mask) {
                        mask.style.display = 'none';
                        mask.remove();
                    });
                    var modals = document.querySelectorAll('[class*="modal"], [class*="dialog"]');
                    modals.forEach(function(modal) {
                        modal.style.display = 'none';
                    });
                """)
                self.log_success("Modal forzado a cerrar con JavaScript")
                time.sleep(1)
                return True
            except:
                pass

            self.log_info("No se encontro modal activo")
            return False

        except Exception as e:
            self.log_warning(f"Error al intentar cerrar modal: {str(e)}")
            return False

    def login(self):
        """Realiza login con Player ID"""
        self.log_info(f"Abriendo {self.url}")
        self.driver.get(self.url)

        try:
            # Esperar Vue.js
            self.wait_for_vue()
            self.take_screenshot("step_01_inicial")

            # Buscar campo de Player ID
            self.log_info("Buscando campo de Player ID...")
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")

            if not inputs:
                all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                inputs = [inp for inp in all_inputs if inp.is_displayed()]

            if not inputs:
                self.log_error("No se encontro el campo de Player ID")
                return False

            player_id_field = inputs[0]
            placeholder = player_id_field.get_attribute('placeholder') or ''
            self.log_success(f"Campo encontrado: '{placeholder}'")

            # Ingresar Player ID
            self.log_info(f"Ingresando Player ID: {self.player_id}")
            player_id_field.click()
            time.sleep(0.5)
            player_id_field.clear()
            player_id_field.send_keys(self.player_id)
            time.sleep(0.5)
            self.log_success("Player ID ingresado correctamente")

            self.take_screenshot("step_02_player_id_ingresado")

            # Buscar botón de login
            self.log_info("Buscando boton de login...")
            clickables = self.find_all_clickables()
            self.log_info(f"Encontrados {len(clickables)} elementos clickeables")

            login_button = None
            for elem in clickables:
                text = elem.text.strip().lower()
                if text and ('login' in text or 'iniciar' in text or 'sesion' in text):
                    login_button = elem
                    self.log_success(f"Boton encontrado: '{elem.text}'")
                    break

            if not login_button:
                self.log_error("No se encontro el boton de login")
                return False

            # Hacer clic en login
            self.log_info("Haciendo clic en boton de login...")
            login_button.click()
            self.log_success("Clic realizado")

            # Esperar respuesta
            self.log_info("Esperando respuesta del servidor (7 segundos)...")
            time.sleep(7)

            self.take_screenshot("step_03_despues_login")
            self.log_success("Login completado exitosamente")

            return True

        except Exception as e:
            self.log_error(f"Error en login: {str(e)}")
            self.take_screenshot("error_login")
            return False

    def redeem_code(self, code):
        """Canjea un código de regalo"""
        self.logger.info("\n" + "="*60)
        self.logger.info(f"CANJEANDO CODIGO: {code}")
        self.logger.info("="*60)

        try:
            # Esperar actualización
            self.log_info("Esperando actualizacion de la pagina...")
            time.sleep(3)

            # Buscar campo de Gift Code
            self.log_info("Buscando campo de Gift Code...")
            all_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")

            if not all_inputs:
                all_inputs = self.driver.find_elements(By.TAG_NAME, "input")

            visible_inputs = []
            for i, inp in enumerate(all_inputs):
                try:
                    if inp.is_displayed():
                        placeholder = inp.get_attribute('placeholder') or ''
                        maxlength = inp.get_attribute('maxlength') or ''
                        self.log_info(f"Input {i}: placeholder='{placeholder}', maxlength='{maxlength}'")
                        visible_inputs.append(inp)
                except:
                    continue

            self.log_info(f"Total: {len(visible_inputs)} inputs visibles")

            # Buscar campo de gift code
            gift_code_field = None

            # Por maxlength="20"
            for inp in visible_inputs:
                if inp.get_attribute('maxlength') == '20':
                    gift_code_field = inp
                    self.log_success("Campo encontrado por maxlength=20")
                    break

            # Por placeholder
            if not gift_code_field:
                for inp in visible_inputs:
                    placeholder = inp.get_attribute('placeholder') or ''
                    if 'codigo' in placeholder.lower() or 'code' in placeholder.lower():
                        gift_code_field = inp
                        self.log_success("Campo encontrado por placeholder")
                        break

            # Primer input visible
            if not gift_code_field and visible_inputs:
                gift_code_field = visible_inputs[0]
                self.log_warning("Usando primer input visible")

            if not gift_code_field:
                self.log_error("No se encontro el campo de Gift Code")
                self.take_screenshot("error_no_gift_field")
                return False

            # Ingresar código
            self.log_info(f"Ingresando codigo: {code}")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", gift_code_field)
            time.sleep(0.5)

            gift_code_field.click()
            time.sleep(0.5)
            gift_code_field.clear()
            time.sleep(0.3)
            gift_code_field.send_keys(code)
            time.sleep(1)
            self.log_success("Codigo ingresado correctamente")

            self.take_screenshot(f"step_04_codigo_{code}_ingresado")

            # Buscar botón de confirmar
            self.log_info("Buscando boton de confirmar...")
            clickables = self.find_all_clickables()

            confirm_button = None
            for elem in clickables:
                try:
                    text = elem.text.strip().lower()
                    if text and ('confirm' in text or 'confirmar' in text):
                        class_attr = elem.get_attribute('class') or ''
                        if 'disabled' not in class_attr.lower():
                            confirm_button = elem
                            self.log_success(f"Boton encontrado: '{elem.text}'")
                            break
                except:
                    continue

            if not confirm_button:
                self.log_error("No se encontro el boton de confirmar")
                return False

            # Hacer clic en confirmar
            self.log_info("Haciendo clic en boton de confirmar...")
            confirm_button.click()
            self.log_success("Clic realizado")

            # Esperar respuesta
            self.log_info("Esperando respuesta del servidor (5 segundos)...")
            time.sleep(5)

            self.take_screenshot(f"step_05_resultado_{code}")

            # Analizar resultado
            page_text = self.driver.page_source.lower()

            result_success = False
            if any(word in page_text for word in ['success', 'exitoso', 'mail', 'correo']):
                self.log_success(f"Codigo {code} canjeado exitosamente!")
                result_success = True
            elif any(word in page_text for word in ['error', 'not found', 'no existe']):
                self.log_error(f"Error al canjear codigo {code}")
                result_success = False
            else:
                self.log_warning("No se pudo determinar el resultado con certeza")
                result_success = True

            # Cerrar modal si existe (importante para el siguiente codigo)
            self.dismiss_modal()

            return result_success

        except Exception as e:
            self.log_error(f"Error al canjear: {str(e)}")
            self.take_screenshot(f"error_redeem_{code}")
            return False

    def close(self):
        """Cierra el navegador"""
        self.log_info("Cerrando navegador...")
        try:
            self.driver.quit()
            self.log_success("Navegador cerrado correctamente")
        except:
            pass


if __name__ == "__main__":
    try:
        with open('login_id.txt', 'r') as f:
            player_id = f.read().strip()
        if not player_id:
            print("[ERROR] El archivo login_id.txt esta vacio")
            sys.exit(1)
    except FileNotFoundError:
        print("[ERROR] No se encontro el archivo login_id.txt")
        sys.exit(1)

    codes = fetch_active_gift_codes()
    if not codes:
        print("[ERROR] No se pudieron obtener codigos activos")
        print("Verifica tu conexion o visita: https://kingshot.net/gift-codes")
        sys.exit(1)

    headless = True
    if '--visible' in sys.argv:
        headless = False

    print("="*70)
    print("BOT DE CODIGOS DE REGALO - KINGSHOT")
    print("="*70)
    print(f"Player ID: {player_id}")
    print(f"Codigos a canjear: {len(codes)}")
    for i, code in enumerate(codes, 1):
        print(f"  {i}. {code}")
    print("="*70)
    print()

    bot = KingshotBotHeadless(player_id, headless=headless)

    try:
        if not bot.login():
            bot.log_error("Login fallido. Abortando.")
            bot.close()
            sys.exit(1)

        successful = 0
        failed = 0

        for code in codes:
            if bot.redeem_code(code):
                successful += 1
            else:
                failed += 1

            if len(codes) > 1:
                time.sleep(3)

        bot.logger.info("\n" + "="*70)
        bot.logger.info("RESUMEN FINAL")
        bot.logger.info("="*70)
        bot.logger.info(f"[+] Exitosos: {successful}")
        bot.logger.info(f"[-] Fallidos: {failed}")
        bot.logger.info(f"[*] Total: {successful + failed}")
        bot.logger.info("="*70)

        bot.log_success("Proceso completado!")

    except KeyboardInterrupt:
        bot.log_warning("Proceso interrumpido por el usuario")
    except Exception as e:
        bot.log_error(f"Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        bot.close()

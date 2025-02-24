import os
import logging
from flask import Flask, request, jsonify
from escpos.printer import Network
from PIL import Image
import io
import base64

# Configure logging based on add-on option
enable_debug = os.getenv("enable_debug", "False").lower() == "true"
logging.basicConfig(level=logging.DEBUG if enable_debug else logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Read configuration from environment variables (set by Home Assistant)
PRINTER_IP = os.getenv("printer_ip", "192.168.1.100")
PRINTER_PORT = int(os.getenv("printer_port", 9100))
WEB_PORT = int(os.getenv("web_port", 5000))

def get_printer():
    try:
        printer = Network(PRINTER_IP, port=PRINTER_PORT, timeout=10)
        return printer
    except Exception as e:
        logger.error("Error connecting to printer: %s", e)
        return None

@app.route('/print/text', methods=['POST'])
def print_text():
    data = request.get_json()
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "Missing 'text' parameter"}), 400
    printer = get_printer()
    if not printer:
        return jsonify({"error": "Printer not available"}), 500
    try:
        printer.text(text + "\n")
        printer.cut()
        return jsonify({"status": "Printed text successfully"}), 200
    except Exception as e:
        logger.exception("Error printing text")
        return jsonify({"error": str(e)}), 500

@app.route('/print/image', methods=['POST'])
def print_image():
    data = request.get_json()
    image_data = data.get("image")
    if not image_data:
        return jsonify({"error": "Missing 'image' parameter (base64 encoded)"}), 400
    try:
        # Decode the base64 image data
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        return jsonify({"error": "Invalid image data: " + str(e)}), 400
    printer = get_printer()
    if not printer:
        return jsonify({"error": "Printer not available"}), 500
    try:
        # Optionally convert image to a mode suitable for printing
        image = image.convert("L")
        printer.image(image)
        printer.cut()
        return jsonify({"status": "Printed image successfully"}), 200
    except Exception as e:
        logger.exception("Error printing image")
        return jsonify({"error": str(e)}), 500

@app.route('/print/barcode', methods=['POST'])
def print_barcode():
    data = request.get_json()
    barcode = data.get("barcode", "")
    barcode_type = data.get("barcode_type", "CODE39")  # default barcode type
    if not barcode:
        return jsonify({"error": "Missing 'barcode' parameter"}), 400
    printer = get_printer()
    if not printer:
        return jsonify({"error": "Printer not available"}), 500
    try:
        # Send a barcode command
        printer.barcode(barcode, barcode_type)
        printer.cut()
        return jsonify({"status": "Printed barcode successfully"}), 200
    except Exception as e:
        logger.exception("Error printing barcode")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=WEB_PORT)

from flask import Flask, request, jsonify

app = Flask(__name__)

# Global variables 
box_temp = None
frequency = None
power_factor = None
voltage = None
current = None
power = None
energy = None
solar_voltage = None
solar_current = None
solar_power = None
battery_percentage = None
light_intensity = None
battery_voltage = None


@app.route('/esp32-data', methods=['POST'])
def receive_data():
    global box_temp, frequency, power_factor, voltage, current, power, energy
    global solar_voltage, solar_current, solar_power, battery_percentage
    global light_intensity, battery_voltage

    try:
        data = request.get_json()

        # Extract values into separate variables
        box_temp = data.get("BoxTemperature")
        frequency = data.get("Frequency")
        power_factor = data.get("PowerFactor")
        voltage = data.get("Voltage")
        current = data.get("Current")
        power = data.get("Power")
        energy = data.get("Energy")
        solar_voltage = data.get("SolarVoltage")
        solar_current = data.get("solarCurrent")
        solar_power = data.get("solarPower")
        battery_percentage = data.get("batteryPercentage")
        light_intensity = data.get("lightIntensity")
        battery_voltage = data.get("batteryVoltage")

        # Debug print
        print("📩 Data received from ESP32:")
        print(f"Box Temp: {box_temp} °C")
        print(f"Voltage: {voltage} V")
        print(f"Current: {current} A")
        print(f"Power: {power} W")
        print(f"Energy: {energy} Wh")
        print(f"Frequency: {frequency} Hz")
        print(f"Power Factor: {power_factor}")
        print(f"Solar: {solar_voltage} V, {solar_current} mA, {solar_power} mW")
        print(f"Battery: {battery_voltage} V, {battery_percentage} %")
        print(f"Light Intensity: {light_intensity} Lux")

    except Exception as e:
        print("❌ Error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/')
def home():
    return "ESP32 API is running. Send data to /esp32-data 🚀"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

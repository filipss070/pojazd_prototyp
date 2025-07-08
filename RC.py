import network
import socket
import time
from machine import Pin, ADC, PWM

led = Pin("LED", Pin.OUT)

# Motor setup
ENABLE_A = Pin(3, Pin.OUT)
PHASE_A =  PWM(Pin(2))
ENABLE_B = Pin(7, Pin.OUT)
PHASE_B = PWM(Pin(6))
MODE = Pin(4, Pin.OUT)
PIN_16 = Pin(16, Pin.OUT)

PHASE_A.freq(200000)
PHASE_B.freq(200000)

MODE.value(1)
PIN_16.value(0)
ENABLE_A.value(1)
ENABLE_B.value(1)

# Boot indicator: blink 3x
for _ in range(3):
    led.toggle()
    time.sleep(0.2)

PHASE_A.duty_u16(int(65535 * 0.5))
PHASE_B.duty_u16(int(65535 * 0.5))

ssid = "wruuum_wruuum"
password = "WRUUUM123"

def ap_setup():
    
    ap = network.WLAN(network.AP_IF)
    ap.config(ssid=ssid, password=password)
    ap.active(True)

    while ap.active() == False:
        print("Initialising access point...")
        time.sleep(1)
        
    
    print("AP is operational, ip = ", ap.ifconfig()[0])


def open_socket():

    address = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.bind(address)
    s.listen(1)

    return (s)


def webpage():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {
                margin: 0;
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                background: #f4f4f4;
                font-family: sans-serif;
                flex-direction: column;
            }
            #sliderBox {
                width: 80vmin;
                height: 80vmin;
                background: #eee;
                position: relative;
                border: 2px solid #aaa;
                border-radius: 50%;
            }
            #knob {
                width: 5vmin;
                height: 5vmin;
                background: #4285f4;
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                border-radius: 50%;
                cursor: pointer;
            }
            p {
                margin-top: 20px;
                font-size: 1.5em;
            }
        </style>
    </head>
    <body>
        <div id="sliderBox">
            <div id="knob"></div>
        </div>
        <p>X: <span id="xVal">0</span> | Y: <span id="yVal">0</span></p>

        <script>
        const knob = document.getElementById("knob");
        const box = document.getElementById("sliderBox");
        const xVal = document.getElementById("xVal");
        const yVal = document.getElementById("yVal");

        const boxSize = box.offsetWidth;
        const center = boxSize / 2;
        const knobSize = knob.offsetWidth;
        const knobOffset = knobSize / 2;
        const maxRadius = center - knobOffset;

        let dragging = false;

        knob.addEventListener("mousedown", () => dragging = true);
        document.addEventListener("mouseup", () => {
            dragging = false;
            knob.style.left = "50%";
            knob.style.top = "50%";
            xVal.textContent = "0";
            yVal.textContent = "0";
            fetch('/0?0');
        });

        document.addEventListener("mousemove", (e) => {
            if (!dragging) return;

            const rect = box.getBoundingClientRect();
            let x = e.clientX - rect.left - center;
            let y = e.clientY - rect.top - center;

            const distance = Math.sqrt(x*x + y*y);
            if (distance > maxRadius) {
                const scale = maxRadius / distance;
                x *= scale;
                y *= scale;
            }

            knob.style.left = (center + x) + "px";
            knob.style.top = (center + y) + "px";

            const xPercent = Math.round((x / maxRadius) * 100);
            const yPercent = Math.round((-y / maxRadius) * 100); // inverted Y

            xVal.textContent = xPercent;
            yVal.textContent = yPercent;

            fetch('/' + xPercent + '?' + yPercent);
        });
        </script>
    </body>
    </html>
    """
    return str(html)


ap_setup()
s = open_socket()

try: 
    while True:
        
        client = s.accept()[0]
        request = client.recv(1024)
        request = str(request)
        X_VEL = "0"
        Y_VEL = "0"
        V_Y = 0
        V_X = 0
        
        try:
            request = request.split()[1]
            X_VEL, Y_VEL = request.split("?")
            X_VEL = X_VEL.strip("/ ")
            Y_VEL = Y_VEL.strip("/ ")
            print(X_VEL, Y_VEL)
            V_Y = abs(int(int(Y_VEL)*196.605))
            V_X = abs(int(int(X_VEL)*196.605/2))
        except:
            pass
        
        if int(Y_VEL) >= 0:
            if int(X_VEL) >= 0:
                PHASE_A.duty_u16(45874 + V_Y)
                PHASE_B.duty_u16(45874 + V_Y - V_X)
            elif int(X_VEL) < 0:
                PHASE_A.duty_u16(45874 + V_Y - V_X)
                PHASE_B.duty_u16(45874 + V_Y)
                
        if int(Y_VEL) < 0:
            if int(X_VEL) >= 0:
                PHASE_A.duty_u16(19661 - V_Y)
                PHASE_B.duty_u16(19661 - V_Y + V_X)
            elif int(X_VEL) < 0:
                PHASE_A.duty_u16(19661 - V_Y + V_X)
                PHASE_B.duty_u16(19661 - V_Y)
        

        if int(X_VEL) == 0 and int(Y_VEL) == 0:
            PHASE_A.duty_u16(int(65535 * 0.5))
            PHASE_B.duty_u16(int(65535 * 0.5))

        html = webpage()
        client.send("HTTP/1.1 200 OK\r\nContent-type: text/html\r\n\r\n")
        client.send(html)
        client.close()
    

except OSError as e:
    client.close()
    print("Error: connection closed")
/* Pulse Generator to test AD2 Trigger/Timestamp recorder.
 * 
 * Generate a square pulse on one pin.
 * And additional synchronous LED pulse on separate pin.
 * 
 * Arduino 328 P clock speed = 16MHz
 * max speed ~16 instructions per microsecond
 * 
 * Doug Brantner 2/25/2022
 */


// NOTE: for delayMicroseconds() - 
// Largest value that will produce an accurate delay is 16383

// TODO for LED to be visible we may need LED duration > Pulse Width...

long TR_DELAY = 2000;  // microseconds between pulses
// average expected ~2-4 MILLIseconds MRI TR

long PULSE_WIDTH = 1; // microseconds for high pulse
// (TODO will this work? too small?)
        

// TODO make these in the same block so we can just write both at once (bitwise/registerwise)
int TRIGGER_OUT_PIN = 2;
int LED_PIN = 3;


void setup() {
  // put your setup code here, to run once:

  pinMode(TRIGGER_OUT_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);

  // TODO pullups? add resistors on outputs?

  digitalWrite(TRIGGER_OUT_PIN, LOW);
  digitalWrite(LED_PIN, LOW):

}

void loop() {
  // put your main code here, to run repeatedly:

  digitalWrite(TRIGGER_OUT_PIN, HIGH);
  digitalWrite(LED_PIN, HIGH):
  
  delayMicroseconds(PULSE_WIDTH);
  
  digitalWrite(TRIGGER_OUT_PIN, LOW);
  digitalWrite(LED_PIN, LOW):

  delayMicroseconds(TR_DELAY);
}

float Vref = 3.3;            // tensione riferimento ADC
int ADC_resolution = 1023;   // risoluzione ADC 10 bit
int rawValue;                // valore letto ADC

float voltage;               // tensione in ingresso ADC (segnale amplificato)
float ecgValue;              // valore stimato del segnale ECG in mV (prima del guadagno)
const float Gain = 500.0;    // guadagno del sensore
const float Voffset = 1;  // offset di metà scala (metà di Vref, perché segnale oscillante)

void setup() {
  Serial.begin(9600);
}

void loop() {
  rawValue = analogRead(A0);

  // Calcolo tensione ingresso ADC
  voltage = (rawValue * Vref) / ADC_resolution;  // in Volt

  // Calcola valore ECG reale (in mV) togliendo offset e dividendo per guadagno
  ecgValue = ((voltage - Voffset) * 1000) / Gain;  // in mV

  unsigned long timestamp = millis();
 
  
  Serial.print(timestamp);
  Serial.print(",");
  
  Serial.println(ecgValue, 3);  // stampa con 3 decimali

  delay(1); // sampling a 1000 Hz circa
}

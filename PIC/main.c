#include <18F45K50.h>          // Inclusión de la librería del microcontrolador

// Configuración del hardware interno (¡Fusibles corregidos para CCS C!)
#device ADC=10                 // Configuramos el ADC para resolución de 10 bits (0 a 1023)
#fuses INTRC_IO, NOMCLR, NOWDT, NOLVP // Reloj interno, sin Reset externo, sin Watchdog, sin LVP
#use delay(clock=8000000)      // Configuramos el reloj interno a 8 MHz
#use rs232(baud=9600, xmit=PIN_C6, rcv=PIN_C7, stream=UART1) // Configuración del puerto serial

void main() {
    // Declaración de variables
    float voltaje = 0.0;
    int16 lectura_adc = 0;     // Variable de 16 bits para almacenar el resultado de 10 bits

    // Configuración de los puertos analógicos
    setup_adc_ports(sAN0);        // Declaramos el pin RA0 (AN0) como entrada analógica
    setup_adc(ADC_CLOCK_INTERNAL); // Usamos el reloj interno para la conversión

    // Bucle infinito (El sistema siempre está monitoreando)
    while(TRUE) {
        
        set_adc_channel(0);       // Le decimos al multiplexor interno que escuche el canal AN0
        delay_us(20);             // Pequeño retardo de seguridad para que el capacitor interno se cargue
        
        // Adquisición de datos
        lectura_adc = read_adc(); // Leemos el valor del voltaje (devuelve un número del 0 al 1023)
        
        // Transformación de señal a valor físico (Voltaje)
        voltaje = ((float)lectura_adc * 5.0) / 1023.0;
        
        // Transmisión Serial hacia Python
        printf("%.2f\r\n", voltaje);
        
        // Retardo de muestreo
        delay_ms(500);            // Esperamos medio segundo antes de enviar el siguiente dato
    }
}
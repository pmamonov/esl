#include <avr/io.h>
#include <avr/interrupt.h>
#include <util/delay.h>
#include "usbdrv.h"

#define CMD_STOP 0
#define CMD_START 1
#define CMD_PARAMS 2
#define CMD_SINGLE 3
#define SINGLE 2

#define ODDR DDRB
#define OPORT PORTB
#define OPIN 0

#if defined (__AVR_ATmega8__)
	#define SSPORT PORTB
	#define SSDDR DDRB
	#define SSPIN 2
#elif defined (__AVR_ATmega32__)
	#define SSPORT PORTB
	#define SSDDR DDRB
	#define SSPIN 4
#endif


typedef struct {
	unsigned int t;
	unsigned int n;
	unsigned int t1;
	unsigned int w;
	unsigned int v;
} StimParam;

volatile StimParam sparam = {476, 2, 46, 23, 0};
volatile uchar bytesLeft;
volatile uchar run;

volatile unsigned int n;
volatile unsigned int CNTVAL1;
volatile unsigned int CNTVAL2;
volatile unsigned int CNTVAL3;

#define SPI_PORT PORTB
#if defined(__AVR_ATmega8__)
#define SPI_MOSI 3
#define SPI_CLK 5
#elif defined(__AVR_ATmega32__)
#define SPI_MOSI 5
#define SPI_CLK 7
#endif

#define SPI_CLK_DELAY4 0.25

inline void spi_transmit(uint8_t b){
  uint8_t i=8;
  while (i--){
    (b&(1<<i)) ? (SPI_PORT|=1<<SPI_MOSI) : (SPI_PORT&=~(1<<SPI_MOSI));
    _delay_ms(SPI_CLK_DELAY4);
    SPI_PORT |= 1<<SPI_CLK;
    _delay_ms(2*SPI_CLK_DELAY4);
    SPI_PORT &= ~(1<<SPI_CLK);
    _delay_ms(SPI_CLK_DELAY4);
  }
}

inline void start(){
		SSPORT &= ~(1<<SSPIN);
/*
		SPDR=sparam.v>>6;
	  while (!(SPSR & (1<<SPIF)));//wait for transmission to finish
		SPDR=sparam.v<<2;
	  while (!(SPSR & (1<<SPIF)));//wait for transmission to finish
*/
    spi_transmit(sparam.v>>6);
    spi_transmit(sparam.v<<2);

		SSPORT |= 1<<SSPIN;

		n=sparam.n;
		CNTVAL1 = (0xffff-sparam.w)+1;
		CNTVAL2 = (sparam.t1-sparam.w) ? (0xffff-(sparam.t1-sparam.w))+1 : 0xffff;
		CNTVAL3 = (sparam.t-(sparam.n-1)*sparam.t1-sparam.w) ? (0xffff-(sparam.t-(sparam.n-1)*sparam.t1-sparam.w))+1 : 0xffff;

		OPORT |= (1<<OPIN);
    TCNT1 = CNTVAL1;
    TIFR = 1<<TOV1;
		TIMSK |= (1<<TOIE1);
}

inline void stop(){
		TIMSK &= ~(1<<TOIE1);
		OPORT &= ~(1<<OPIN);
    run=0;
}

ISR(TIMER1_OVF_vect){
	if (OPORT & (1<<OPIN)){
		OPORT &= ~(1<<OPIN);
		if (--n==0){
			TCNT1=CNTVAL3;
			n=sparam.n;
      if (run & SINGLE) stop();
		}
    else{TCNT1=CNTVAL2;}
	}
	else{
		TCNT1 = CNTVAL1;
		OPORT |= 1<<OPIN;
	}
}

usbMsgLen_t usbFunctionSetup(uchar data[8]) {
	usbRequest_t *rq = (void *)data;
  switch (rq->bRequest){
		case CMD_STOP:
		run=0;
		case CMD_PARAMS:
		stop();
		if (rq->bRequest == CMD_STOP) break;

		bytesLeft=sizeof(sparam);
		return USB_NO_MSG;

		case CMD_START:
		run=1;
		start();
		break;

		case CMD_SINGLE:
		run=3;
		start();
		break;

		default:
		break;
  }
  return 0;
}

uchar usbFunctionWrite(uchar *data, uchar l){
	int i;
	if (l>bytesLeft) l=bytesLeft;
	for (i=0; i<l; i++) ((uchar*)(&sparam))[sizeof(sparam)-bytesLeft--]=data[i];
	if (!bytesLeft && run) start();
	return bytesLeft==0;
}

void main(void){
	TCCR1B |= 4<<CS10;// 1/256
//	TIMSK |= 1<<TOIE1;
	run=0;
	ODDR |= 1<<OPIN;

#if defined (__AVR_ATmega8__)
	DDRB |= (1<<5)|(1<<3)|(1<<2);
#elif defined (__AVR_ATmega32__)
	DDRB |= (1<<7)|(1<<5)|(1<<4);
#endif
//  SPCR = (1<<SPE)|(1<<MSTR)|(3<<SPR0);// f=fosc/128 == ~100kHz

	usbInit();
	usbDeviceDisconnect();  /* enforce re-enumeration, do this while interrupts are disabled! */
	_delay_ms(250);
	usbDeviceConnect();
	sei();
	while(1){
		usbPoll();
	}
}


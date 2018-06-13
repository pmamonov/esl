#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/eeprom.h>
#include <util/delay.h>
#include "usbdrv.h"

#define VER	1

#define CMD_STOP	0
#define CMD_START	1
#define CMD_PARAMS	2
#define CMD_SINGLE	3
#define CMD_GETPARAMS	4
#define CMD_STORE	5
#define CMD_LOAD	6
#define CMD_TRIG_EN	7
#define CMD_TRIG_DIS	8

#define SINGLE		2

#define ODDR		DDRB
#define OPORT		PORTB
#define OPIN		0

/* Monitor pin */
#ifdef __AVR_ATmega8__
	#define MDDR		DDRB
	#define MPORT		PORTB
	#define MPIN		4
#endif

/* Trigger pin */
#define TDDR		DDRC
#define TPORT		PORTC
#define TPIN		PINC
#define TBIT		1

#if defined (__AVR_ATmega8__)
	#define SSPORT	PORTB
	#define SSDDR	DDRB
	#define SSPIN	2
#elif defined (__AVR_ATmega32__)
	#define SSPORT	PORTB
	#define SSDDR	DDRB
	#define SSPIN	4
#endif


typedef struct {
	unsigned int ver;
	unsigned long t;
	unsigned int n;
	unsigned int t1;
	unsigned int w;
	unsigned int v;
} StimParam;

volatile StimParam sparam = {VER, 476, 2, 46, 23, 0};
volatile uchar bytesLeft;
volatile uchar run, trig_en;

volatile unsigned int n;
volatile unsigned int CNTVAL1;
volatile unsigned int CNTVAL2;
volatile unsigned long CNTVAL3, T;

#define SPI_PORT PORTB

#if defined(__AVR_ATmega8__)
	#define SPI_MOSI	3
	#define SPI_CLK		5
#elif defined(__AVR_ATmega32__)
	#define SPI_MOSI	5
	#define SPI_CLK		7
#endif

#define SPI_CLK_DELAY4 0.25

inline void parstore()
{
	eeprom_write_dword(0, 0xdeadbeefUL);
	eeprom_write_block((void *)&sparam, (void *)4, sizeof(sparam));
}

inline void parload()
{
	if (eeprom_read_dword(0) == 0xdeadbeefUL)
		eeprom_read_block((void *)&sparam, (void *)4, sizeof(sparam));
	sparam.ver = VER;
}

inline void spi_transmit(uint8_t b)
{
	uint8_t i=8;
	while (i--) {
		if (b & (1 << i))
			SPI_PORT |= 1 << SPI_MOSI;
		else
			SPI_PORT &= ~(1 << SPI_MOSI);

		_delay_ms(SPI_CLK_DELAY4);

		SPI_PORT |= 1 << SPI_CLK;

		_delay_ms(2*SPI_CLK_DELAY4);

		SPI_PORT &= ~(1 << SPI_CLK);

		_delay_ms(SPI_CLK_DELAY4);
	}
}

inline void start()
{
	SSPORT &= ~(1 << SSPIN);
/*
	SPDR=sparam.v>>6;
	while (!(SPSR & (1<<SPIF)));//wait for transmission to finish
	SPDR=sparam.v<<2;
	while (!(SPSR & (1<<SPIF)));//wait for transmission to finish
*/
	spi_transmit(sparam.v >> 6);
	spi_transmit(sparam.v << 2);

	SSPORT |= 1 << SSPIN;

	/* validate parameters */
	if (!sparam.n)
		sparam.n = 1;
	if (!sparam.t)
		sparam.t = 1;
	if (!sparam.t1)
		sparam.t1 = 1;
	if (!sparam.w)
		sparam.w = 1;
	if (sparam.w >= sparam.t1)
		sparam.t1 = sparam.w + 1;
	if (sparam.t1 * sparam.n > sparam.t)
		sparam.t = sparam.t1 * sparam.n + 1;

	T = 0;
	n = sparam.n;
	CNTVAL1 = 0x10000ul - sparam.w;
	CNTVAL2 = 0x10000ul - (sparam.t1 - sparam.w);
	CNTVAL3 = sparam.t - ((sparam.n - 1) * sparam.t1 + sparam.w);

	OPORT |= (1<<OPIN);
	MPORT |= (1 << MPIN);

	TCNT1 = CNTVAL1;
	TIFR = 1 << TOV1;
	TIMSK |= (1 << TOIE1);
}

inline void stop()
{
	TIMSK &= ~(1 << TOIE1);
	OPORT &= ~(1 << OPIN);
	MPORT &= ~(1 << MPIN);
	run=0;
}


usbMsgLen_t usbFunctionSetup(uchar data[8]) {
	usbRequest_t *rq = (void *)data;

	switch (rq->bRequest) {

	case CMD_STOP:
		run=0;

	case CMD_PARAMS:
		stop();
		if (rq->bRequest == CMD_STOP)
			break;

		bytesLeft = sizeof(sparam);
		return USB_NO_MSG;

	case CMD_START:
		run=1;
		start();
		break;

	case CMD_SINGLE:
		run=3;
		start();
		break;

	case CMD_GETPARAMS:
		usbMsgPtr = (uchar *)&sparam;
		return sizeof(sparam);

	case CMD_STORE:
		parstore();
		break;

	case CMD_LOAD:
		parload();
		break;

	case CMD_TRIG_EN:
		trig_en = 1;
		break;

	case CMD_TRIG_DIS:
		trig_en = 0;
		break;

	default:
		break;
	}
	return 0;
}

uchar usbFunctionWrite(uchar *data, uchar l)
{
	uchar *dst = (uchar *)&sparam;
	int i, sz = sizeof(sparam);

	if (l > bytesLeft)
		l = bytesLeft;
	for (i = 0; i < l; i++)
		dst[sz - bytesLeft--] = data[i];

	if (!bytesLeft) {
		sparam.ver = VER;
		if (run)
			start();
	}

	return bytesLeft == 0;
}

int main(void)
{
	TCCR1B |= 4 << CS10;// 1/256
//	TIMSK |= 1<<TOIE1;
	run=0;
	ODDR |= 1 << OPIN;
	MDDR |= 1 << MPIN;
	TDDR &= ~(1 << TBIT);
	TPORT |= 1 << TBIT; /* pull up */

#if defined (__AVR_ATmega8__)
	DDRB |= (1 << 5) | (1 << 3) | (1 << 2);
#elif defined (__AVR_ATmega32__)
	DDRB |= (1 << 7) | (1 << 5) | (1 << 4);
#endif
//	SPCR = (1<<SPE)|(1<<MSTR)|(3<<SPR0);// f=fosc/128 == ~100kHz

	usbInit();
	/* enforce re-enumeration, do this while interrupts are disabled! */
	usbDeviceDisconnect();
	_delay_ms(250);
	usbDeviceConnect();

	sei();

	while(1) {
		if (trig_en && !run &&
		    0 == (TPIN & (1 << TBIT))) {
			run = 3;
			start();
		}
		usbPoll();
	}
}

ISR(TIMER1_OVF_vect)
{
	if (OPORT & (1 << OPIN)) {
		OPORT &= ~(1 << OPIN);
		if (--n == 0) {
			if (CNTVAL3 < 0x10000ul) {
				TCNT1 = 0x10000ul - CNTVAL3;
				T = 0;
			} else
				T = CNTVAL3 - 0x10000ul;
			n = sparam.n;
		} else
			TCNT1 = CNTVAL2;
	} else {
		if (T == 0) {
			if (n == sparam.n && (run & SINGLE)) {
				stop();
				return;
			}
			OPORT |= 1 << OPIN;
			TCNT1 = CNTVAL1;
			return;
		}

		if (T > 0x10000ul) {
			T -= 0x10000ul;
		} else {
			TCNT1 = 0x10000 - T;
			T = 0;
		}
	}
}


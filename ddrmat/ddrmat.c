/*
 * PSX Parallel Port DDR mat module
 *
 * based on gamecon.c, v1.14 2001/04/29 22:42:14
 *  Copyright (c) 1999-2001 Vojtech Pavlik
 *  which was based from:
 *  	Andree Borrmann		John Dahlstrom
 *  	David Kuder		Nathan Hand
 */

/*
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or 
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
 */

#include <linux/kernel.h>
#include <linux/delay.h>
#include <linux/module.h>
#include <linux/init.h>
#include <linux/parport.h>
#include <linux/input.h>

MODULE_AUTHOR("Vojtech Pavlik <vojtech@suse.cz>, Brendan Becker <tgz@orotech.net>");
MODULE_LICENSE("GPL");
MODULE_PARM(gc, "2-6i");
MODULE_PARM(gc_2,"2-6i");
MODULE_PARM(gc_3,"2-6i");

#define GC_PSX		7
#define GC_MAX		7

#define GC_REFRESH_TIME	HZ/100
 
struct gc {
	struct pardevice *pd;
	struct input_dev dev[5];
	struct timer_list timer;
	unsigned char pads[GC_MAX + 1];
	int used;
};

static struct gc *gc_base[3];

static int gc[] __initdata = { -1, 0, 0, 0, 0, 0 };
static int gc_2[] __initdata = { -1, 0, 0, 0, 0, 0 };
static int gc_3[] __initdata = { -1, 0, 0, 0, 0, 0 };

static int gc_status_bit[] = { 0x40, 0x80, 0x20, 0x10, 0x08 };

static char *gc_names[] = { NULL, "SNES pad", "NES pad", "NES FourPort", "Multisystem joystick",
				"Multisystem 2-button joystick", "N64 controller", "DDR mat" };

/*
 * PSX support
 *
 * See documentation at:
 *	http://www.dim.com/~mackys/psxmemcard/ps-eng2.txt
 *	http://www.gamesx.com/controldata/psxcont/psxcont.htm
 *	ftp://milano.usal.es/pablo/
 *	
 */

#define GC_PSX_DELAY	10		/* 60 usec */
#define GC_PSX_LENGTH	8		/* talk to the controller in bytes */

#define GC_PSX_MOUSE	1		/* Mouse */
#define GC_PSX_NEGCON	2		/* NegCon */
#define GC_PSX_NORMAL	4		/* Digital / Analog or Rumble in Digital mode  */
#define GC_PSX_ANALOG	5		/* Analog in Analog mode / Rumble in Green mode */
#define GC_PSX_RUMBLE	7		/* Rumble in Red mode */

#define GC_PSX_CLOCK	0x04		/* Pin 4 */
#define GC_PSX_COMMAND	0x01		/* Pin 1 */
#define GC_PSX_POWER	0xf8		/* Pins 5-9 */
#define GC_PSX_SELECT	0x02		/* Pin 3 */

#define GC_PSX_ID(x)	((x) >> 4)	/* High nibble is device type */
#define GC_PSX_LEN(x)	((x) & 0xf)	/* Low nibble is length in words */

static short gc_psx_abs[] = { ABS_X, ABS_Y, ABS_RX, ABS_RY, ABS_HAT0X, ABS_HAT0Y };
static short gc_psx_btn[] = { BTN_TL, BTN_TR, BTN_TL2, BTN_TR2, BTN_A, BTN_B, BTN_X, BTN_Y,
				BTN_START, BTN_SELECT, BTN_THUMBL, BTN_THUMBR };

/*
 * gc_psx_command() writes 8bit command and reads 8bit data from
 * the psx pad.
 */

static int gc_psx_command(struct gc *gc, int b)
{
	int i, cmd, data = 0;

	for (i = 0; i < 8; i++, b >>= 1) {
		cmd = (b & 1) ? GC_PSX_COMMAND : 0;
		parport_write_data(gc->pd->port, cmd | GC_PSX_POWER);
		udelay(GC_PSX_DELAY);
		data |= ((parport_read_status(gc->pd->port) ^ 0x80) & gc->pads[GC_PSX]) ? (1 << i) : 0;
		parport_write_data(gc->pd->port, cmd | GC_PSX_CLOCK | GC_PSX_POWER);
		udelay(GC_PSX_DELAY);
	}
	return data;
}

/*
 * gc_psx_read_packet() reads a whole psx packet and returns
 * device identifier code.
 */

static int gc_psx_read_packet(struct gc *gc, unsigned char *data)
{
	int i, id;
	unsigned long flags;

	parport_write_data(gc->pd->port, GC_PSX_CLOCK | GC_PSX_SELECT | GC_PSX_POWER);	/* Select pad */
	udelay(GC_PSX_DELAY);
	parport_write_data(gc->pd->port, GC_PSX_CLOCK | GC_PSX_POWER);			/* Deselect, begin command */
	udelay(GC_PSX_DELAY);

	__save_flags(flags);
	__cli();

	gc_psx_command(gc, 0x01);							/* Access pad */
	id = gc_psx_command(gc, 0x42);							/* Get device id */
	if (gc_psx_command(gc, 0) == 0x5a) {						/* Okay? */
		for (i = 0; i < GC_PSX_LEN(id) * 2; i++)
			data[i] = gc_psx_command(gc, 0);
	} else id = 0;

	__restore_flags(flags);

	parport_write_data(gc->pd->port, GC_PSX_CLOCK | GC_PSX_SELECT | GC_PSX_POWER);

	return GC_PSX_ID(id);
}

/*
 * gc_timer() reads and analyzes console pads data.
 */

#define GC_MAX_LENGTH 32

static void gc_timer(unsigned long private)
{
	struct gc *gc = (void *) private;
	struct input_dev *dev = gc->dev;
	unsigned char data[GC_MAX_LENGTH];
	int i, j;

/*
 * PSX controllers
 */

	if (gc->pads[GC_PSX]) {

		for (i = 0; i < 5; i++)
	       		if (gc->pads[GC_PSX] & gc_status_bit[i])
				break;

 		switch (gc_psx_read_packet(gc, data)) {

			case GC_PSX_RUMBLE:

				input_report_key(dev + i, BTN_THUMB,  ~data[0] & 0x04);
				input_report_key(dev + i, BTN_THUMB2, ~data[0] & 0x02);

			case GC_PSX_NORMAL:
/*
				input_report_abs(dev + i, ABS_X, 128 + !(data[0] & 0x20) * 127 - !(data[0] & 0x80) * 128);
				input_report_abs(dev + i, ABS_Y, 128 + !(data[0] & 0x40) * 127 - !(data[0] & 0x10) * 128);
				for (j = 0; j < 4; j++)
					input_report_key(dev + i, gc_psx_btn[j], ~data[1] & (1 << j));
*/
				input_report_key(dev + i, BTN_START,  ~data[0] & 0x08);
				input_report_key(dev + i, BTN_SELECT, ~data[0] & 0x01);

        input_report_key(dev+i, BTN_TL, !(data[0] & 0x80));   //left button
        input_report_key(dev+i, BTN_TR, !(data[0] & 0x20));   //right button
        input_report_key(dev+i, BTN_TL2, !(data[0] & 0x40));  //down button
        input_report_key(dev+i, BTN_TR2, !(data[0] & 0x10));  //up button

				break;
		}
	}

	mod_timer(&gc->timer, jiffies + GC_REFRESH_TIME);
}

static int gc_open(struct input_dev *dev)
{
	struct gc *gc = dev->private;
	if (!gc->used++) {
		parport_claim(gc->pd);
		parport_write_control(gc->pd->port, 0x04);
		mod_timer(&gc->timer, jiffies + GC_REFRESH_TIME);
	}
	return 0;
}

static void gc_close(struct input_dev *dev)
{
	struct gc *gc = dev->private;
	if (!--gc->used) {
		del_timer(&gc->timer);
		parport_write_control(gc->pd->port, 0x00);
		parport_release(gc->pd);
	}
}

static struct gc __init *gc_probe(int *config)
{
	struct gc *gc;
	struct parport *pp;
	int i, j, psx;
	unsigned char data[32];

	if (config[0] < 0)
		return NULL;

	for (pp = parport_enumerate(); pp && (config[0] > 0); pp = pp->next)
		config[0]--;

	if (!pp) {
		printk(KERN_ERR "ddrmat.c: no such parport\n");
		return NULL;
	}

	if (!(gc = kmalloc(sizeof(struct gc), GFP_KERNEL)))
		return NULL;
	memset(gc, 0, sizeof(struct gc));

	gc->pd = parport_register_device(pp, "ddrmat", NULL, NULL, NULL, PARPORT_DEV_EXCL, NULL);

	if (!gc->pd) {
		printk(KERN_ERR "ddrmat.c: parport busy already - lp.o loaded?\n");
		kfree(gc);
		return NULL;
	}

	parport_claim(gc->pd);

	init_timer(&gc->timer);
	gc->timer.data = (long) gc;
	gc->timer.function = gc_timer;

	for (i = 0; i < 5; i++) {

		if (!config[i + 1])
			continue;

		if (config[i + 1] < 1 || config[i + 1] > GC_MAX) {
			printk(KERN_WARNING "ddrmat.c: Pad type %d unknown\n", config[i + 1]);
			continue;
		}

                gc->dev[i].private = gc;
                gc->dev[i].open = gc_open;
                gc->dev[i].close = gc_close;

                gc->dev[i].evbit[0] = BIT(EV_KEY) | BIT(EV_ABS);

		for (j = 0; j < 2; j++) {
			set_bit(ABS_X + j, gc->dev[i].absbit);
			gc->dev[i].absmin[ABS_X + j] = -1;
			gc->dev[i].absmax[ABS_X + j] =  1;
		}

		gc->pads[0] |= gc_status_bit[i];
		gc->pads[config[i + 1]] |= gc_status_bit[i];

		switch(config[i + 1]) {

			case GC_PSX:
				
				psx = gc_psx_read_packet(gc, data);

				switch(psx) {
					case GC_PSX_NORMAL:

					case GC_PSX_RUMBLE:

						for (j = 0; j < 6; j++) {
							psx = gc_psx_abs[j];
							set_bit(psx, gc->dev[i].absbit);
							if (j < 4) {
								gc->dev[i].absmin[psx] = 4;
								gc->dev[i].absmax[psx] = 252;
								gc->dev[i].absflat[psx] = 2;
							} else {
								gc->dev[i].absmin[psx] = -1;
								gc->dev[i].absmax[psx] = 1;
							}
						}

						for (j = 0; j < 12; j++)
							set_bit(gc_psx_btn[j], gc->dev[i].keybit);

						break;

					case 0:
						gc->pads[GC_PSX] &= ~gc_status_bit[i];
						printk(KERN_ERR "ddrmat.c: No mat found.\n");
						break;

					default:
						gc->pads[GC_PSX] &= ~gc_status_bit[i];
						printk(KERN_WARNING "ddrmat.c: Unsupported DDR mat %#x,"
							" please report to <tgz@orotech.net>.\n", psx);
				}
				break;
		}

                gc->dev[i].name = gc_names[config[i + 1]];
                gc->dev[i].idbus = BUS_PARPORT;
                gc->dev[i].idvendor = 0x0001;
                gc->dev[i].idproduct = config[i + 1];
                gc->dev[i].idversion = 0x0100;
	}

	parport_release(gc->pd);

	if (!gc->pads[0]) {
		parport_unregister_device(gc->pd);
		kfree(gc);
		return NULL;
	}

	for (i = 0; i < 5; i++) 
		if (gc->pads[0] & gc_status_bit[i]) {
			input_register_device(gc->dev + i);
			printk(KERN_INFO "input%d: DDR mat on %s\n", gc->dev[i].number, gc->pd->port->name);

		}

	return gc;
}

#ifndef MODULE
int __init gc_setup(char *str)
{
	int i, ints[7];
	get_options(str, ARRAY_SIZE(ints), ints);
	for (i = 0; i <= ints[0] && i < 6; i++) gc[i] = ints[i + 1];
	return 1;
}
int __init gc_setup_2(char *str)
{
	int i, ints[7];
	get_options(str, ARRAY_SIZE(ints), ints);
	for (i = 0; i <= ints[0] && i < 6; i++) gc_2[i] = ints[i + 1];
	return 1;
}
int __init gc_setup_3(char *str)
{
	int i, ints[7];
	get_options(str, ARRAY_SIZE(ints), ints);
	for (i = 0; i <= ints[0] && i < 6; i++) gc_3[i] = ints[i + 1];
	return 1;
}
__setup("gc=", gc_setup);
__setup("gc_2=", gc_setup_2);
__setup("gc_3=", gc_setup_3);
#endif

int __init gc_init(void)
{
	gc_base[0] = gc_probe(gc);
	gc_base[1] = gc_probe(gc_2);
	gc_base[2] = gc_probe(gc_3);

	if (gc_base[0] || gc_base[1] || gc_base[2])
		return 0;

	return -ENODEV;
}

void __exit gc_exit(void)
{
	int i, j;

	for (i = 0; i < 3; i++)
		if (gc_base[i]) {
			for (j = 0; j < 5; j++)
				if (gc_base[i]->pads[0] & gc_status_bit[j])
					input_unregister_device(gc_base[i]->dev + j); 
			parport_unregister_device(gc_base[i]->pd);
		}
}

module_init(gc_init);
module_exit(gc_exit);

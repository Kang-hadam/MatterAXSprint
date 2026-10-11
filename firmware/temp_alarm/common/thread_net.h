/*
 * Thread network settings shared by the sensor (dongle) and the LED board (DK).
 */

#ifndef THREAD_NET_H_
#define THREAD_NET_H_

/* The sensor sends each reading to this UDP port on all Thread nodes. */
#define TEMP_UDP_PORT  4242
#define TEMP_UDP_GROUP "ff03::1"

/* Set the fixed test network credentials and start Thread. */
int thread_net_start(void);

#endif /* THREAD_NET_H_ */


/*
 * This is ???????????.
 * ------------------------------------------------------------------
 * Part of "Firmware/API/GUI for x-SLON" project.
 * http://github.com/pmamonov/esl
 * 
 */


#include <stdio.h>
#include <poll.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <sys/time.h>

int main(int argc, char **argv)
{
	struct pollfd pfd = {
		.events = POLLPRI | POLLERR,  
	};
	if (argc < 1)
		return 1;

	pfd.fd = open(argv[1], O_RDONLY);
	if (pfd.fd < 0)
		return 2;
	while (1) {
#define BUF_SZ	4
		char buf[BUF_SZ];
		struct timeval tv;
		
		poll(&pfd, 1, -1);
		gettimeofday(&tv, NULL);
		memset(buf, 0, BUF_SZ);
		lseek(pfd.fd, 0, SEEK_SET);
		read(pfd.fd, buf, BUF_SZ - 1);
		printf("%d.%06d %s", tv.tv_sec, tv.tv_usec, buf);
		fflush(stdout);
	}
	close(pfd.fd);
	return 0;
}

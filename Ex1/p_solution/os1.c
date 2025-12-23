#include <sys/time.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <string.h>

#define STR_SEP " \t\n"

int main(int argc, char *argv[])
{
	setbuf(stdout, NULL);
	char line[2048];
	char* args[200];

	while (1) {
		printf("$$ ");
		if (fgets(line, 2048, stdin) == NULL)
			break;
		int rc = waitpid(-1, NULL, WNOHANG);
		while ((rc != 0) && (rc != -1)) {
			printf("%d\n", rc);
			rc = waitpid(-1, NULL, WNOHANG);
		}

		args[0] = strtok(line, STR_SEP);
		int i = 0;		
		while (args[i] != NULL) {
			++i;
			args[i] = strtok(NULL, STR_SEP);
		}
		if (i == 0)
			continue;

		int bg = 0;
		if (!strcmp(args[i-1], "%")) {
			args[i-1] = NULL;
			bg = 1;
		}

		rc = fork();
		if (rc < 0) {
			perror("fork");
			exit(-1);
		}
		else if (rc == 0) {
			execvp(args[0], args);
			perror("execvp");
			exit(-1);
		}
		else {
			if (!bg)
				waitpid(rc, NULL, 0);
		}
	}
	printf("\n");
	return 0;
}

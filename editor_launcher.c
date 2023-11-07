// This file will run ./python3 ./editor.py replacing the current process

#include <stdio.h>
#include <stdlib.h>

int main()
{
    char *args[] = {"pyw", "./editor.py", NULL};
    execvp(args[0], args);
    return 0;
}